import os
import re
import hashlib
import time
import shutil
import apt_pkg
import eventlet
import tempfile
import traceback
import subprocess

from eventlet import wsgi

from .utils import json_response, parse_repo, parse_querystring
from .exceptions import BaseHttpException, Http400, Http403, Http404, Http405

apt_pkg.init_system()

re_filename = re.compile(r'^(?P<name>[^_]+)_(?P<version>[^_]+)_[^_]+\.deb$')

class Server(object):
    def __init__(self, log, options):
        self.log = log
        self.options = options

        self.log.info("Opening sockets...")
        self.wsgi_socket = eventlet.listen((self.options.bind, self.options.port))

        self.pool = eventlet.GreenPool(10000)

        self.log.info("Sockets established.")

        self.stats = {
            'started': int(time.time()),
            'num_GET': 0,
            'num_PUT': 0,
            'num_POST': 0,
        }

        self.log.info("Initialised")

    def run(self):
        self.log.info("Starting HTTP server")
        self.pool.spawn_n(wsgi.server, self.wsgi_socket, self.handle_wsgi)

        self.log.info("Entering mainloop")

        try:
            self.pool.waitall()
        except (SystemExit, KeyboardInterrupt):
            pass

    def handle_wsgi(self, env, start_response):
        try:
            try:
                fn = getattr(self, 'process_%s' % env['REQUEST_METHOD'])
            except AttributeError:
                raise Http405()

            if not env.get('PATH_INFO'):
                raise Http400()

            return fn(env, start_response)
        except BaseHttpException, e:
            start_response(e.message, [])
            return [e.message]
        except Exception, e:
            self.log.exception("Exception when processing request")
            start_response("500 Internal Server Error", [])
            return [traceback.format_exc()]

    def fullpath_from_uri(self, uri):
        result = os.path.abspath(
            os.path.join(self.options.archive_root, uri.lstrip('/'))
        )

        if not result.startswith(self.options.archive_root):
            raise Http403()

        return os.path.join(self.options.archive_root, uri.lstrip('/'))

    ###########################################################################

    def process_GET(self, env, start_response):
        if env['PATH_INFO'] == '/':
            start_response('200 OK', [])

            with open(os.path.join(self.options.gpg_home, 'pubring.gpg')) as f:
                return [f.read()]

        if env['PATH_INFO'] == '/_stats':
            self.stats.update({
                'uptime': int(time.time() - self.stats['started']),
            })

            return json_response(start_response, self.stats)

        self.stats['num_GET'] += 1

        fullpath = self.fullpath_from_uri(env['PATH_INFO'])

        if not os.path.exists(fullpath):
            raise Http404()

        if os.path.isdir(fullpath):
            raise Http403()

        start_response("200 OK", [])
        with open(fullpath, 'rb') as f:
            return [f.read()]

    def process_POST(self, env, start_response):
        self.stats['num_POST'] += 1

        repo = parse_repo(env)

        self.refresh_repo(repo)

        return json_response(start_response, {
            'repo': repo,
        })

    def process_PUT(self, env, start_response):
        self.stats['num_PUT'] += 1

        try:
            size = int(env['CONTENT_LENGTH'])
        except (ValueError, KeyError):
            raise Http400()

        repo = parse_repo(env)

        f = tempfile.NamedTemporaryFile(delete=False)

        try:
            f.write(env['wsgi.input'].read(size))
            f.flush()
            package, created = self.process_upload(repo, f.name)
        finally:
            try:
                os.unlink(f.name)
            except OSError:
                # We may have moved the file - tempfile with delete=True would
                # blow up in the equivalent place
                pass

        # Pass in ?refresh_repo=0 to skip repo refresh
        if parse_querystring(env).get('refresh_repo') != '0':
            self.refresh_repo(repo)

        return json_response(start_response, {
            'repo': repo,
            'created': created,
            'package': package,
        }, http_header="201 Created" if created else "200 OK")

    ###########################################################################

    def process_upload(self, repo, filename):
        # python-debian does not support xz so we have to do this manually
        def extract(field):
            return subprocess.check_output((
                'dpkg-deb',
                '--field',
                filename,
                field,
            )).strip()

        deb = dict(
            (x, extract(x)) for x in ('Package', 'Version', 'Architecture'),
        )

        # Calculate target filename
        fullpath = os.path.join(
            self.options.archive_root,
            'dists',
            repo,
            'main',
            'binary-%(Architecture)s' % deb \
                if deb['Architecture'] != 'all' else 'arch-all',
            '%(Package)s_%(Version)s_%(Architecture)s.deb' % deb,
        )

        fullpath_parent = os.path.dirname(fullpath)

        # Check first so we don't mask errors creating the directories
        if not os.path.isdir(fullpath_parent):
            os.makedirs(fullpath_parent, mode=0755)

        created = not os.path.exists(fullpath)

        # Move/overwrite the uploaded .deb into place. We use shutil.move as
        # os.rename won't work across filesystems.
        shutil.move(filename, fullpath)

        return deb, created

    def refresh_repo(self, repo):
        repo_dir = os.path.join(self.options.archive_root, 'dists', repo)
        component_dir = os.path.join(repo_dir, 'main')

        # Ensure binary-ARCH dirs exist for all common arches. This ensures we
        # get updated Packages files for all architectures even if they have no
        # files.
        for x in self.options.architectures:
            try:
                os.makedirs(os.path.join(component_dir, 'binary-%s' % x))
            except OSError:
                pass

        # Also create a special "arch-all" directory - APT won't actually
        # access files in this directory, but all the other arches need to see
        # these packages.
        try:
            os.makedirs(os.path.join(component_dir, 'arch-all'))
        except OSError:
            pass

        # Ensure there are only X versions of each package.
        for base, _, filenames in os.walk(component_dir):
            packages = {}

            for filename in filenames:
                m = re_filename.match(filename)
                if m is None:
                    continue

                packages.setdefault(m.group('name'), []).append(
                    (m.group('version'), filename)
                )

            for x in packages.values():
                for _, filename in sorted(
                    x,
                    cmp=lambda x, y: apt_pkg.version_compare(x[0], y[0]),
                    reverse=True,
                )[self.options.max_versions:]:
                    os.unlink(os.path.join(base, filename))

        # Update Packages file for architectures
        for x in self.options.architectures:
            target = os.path.join(component_dir, 'binary-%s' % x, 'Packages.new')

            for cmd in (
                'dpkg-scanpackages -m dists/%(repo)s/main/binary-%(arch)s /dev/null > %(target)s',
                'dpkg-scanpackages -m dists/%(repo)s/main/arch-all /dev/null >> %(target)s',
            ):
                subprocess.check_output(('sh', '-c', cmd % {
                    'repo': repo,
                    'arch': x,
                    'target': target,
                }), cwd=self.options.archive_root)

            for cmd in (
                'bzip2 -9 -c Packages.new > Packages.bz2.new',
                'mv Packages.new Packages',
                'mv Packages.bz2.new Packages.bz2',
            ):
                subprocess.check_output(
                    ('sh', '-c', cmd),
                    cwd=os.path.dirname(target),
                )

        # Generate Release
        release = os.path.join(repo_dir, 'Release')

        with open(release, 'w') as f:
            print >>f, "Archive: %s" % self.options.archive
            print >>f, "Origin: %s" % self.options.origin
            print >>f, "Suite: %s" % repo
            print >>f, "Date: %s" % time.strftime("%a, %d %b %Y %H:%M:%S +0000")
            print >>f, "SHA1:"

            for base, _, filenames in os.walk(component_dir):
                for filename in filenames:
                    if not filename.startswith('Packages'):
                        continue

                    to_hash = os.path.join(base, filename)

                    with open(to_hash) as f2:
                        print >>f, ' %s %d %s' % (
                            hashlib.sha1(f2.read()).hexdigest(),
                            os.path.getsize(to_hash),
                            to_hash[len(repo_dir) + 1:],
                        )

            print >>f, "SHA256:"

            for base, _, filenames in os.walk(component_dir):
                for filename in filenames:
                    if not filename.startswith('Packages'):
                        continue

                    to_hash = os.path.join(base, filename)

                    with open(to_hash) as f2:
                        print >>f, ' %s %d %s' % (
                            hashlib.sha256(f2.read()).hexdigest(),
                            os.path.getsize(to_hash),
                            to_hash[len(repo_dir) + 1:],
                        )


        # Generate Release.gpg
        try:
            # Must remove target or gpg will prompt us whether we want to overwrite
            os.unlink('%s.gpg.new' % release)
        except:
            pass

        subprocess.check_output((
            'gpg',
            '--homedir', self.options.gpg_home,
            '--no-permission-warning',
            '--sign',
            '--detach-sign',
            '--armor',
            '--output', '%s.gpg.new' % release,
            release,
        ))

        os.rename('%s.gpg.new' % release, '%s.gpg' % release)

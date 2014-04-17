=====
APTly
=====

----------------------------------------------------------------------------
Lightweight, standalone RESTful HTTP server for distributing Debian packages
----------------------------------------------------------------------------

APTly is a simple, lightweight HTTP server for storing and distributing custom
Debian packages around your organisation.

Each APTly instance is a HTTP APT repo - simpy point a
``/etc/apt/sources.list`` entry at your instance for instant package
distribution!


Why use APTly?
~~~~~~~~~~~~~~

 * Zero configuration -- just start uploading your packages using HTTP ``PUT``.

 * Integrates better into the Debian system over ``dpkg -i``, especially in
   automatically resolving dependencies and repository pinning.

 * Supports arbitrary repositories - one APTly instance can handle multiple
   repositories. This allows you to keep "live" and "staging" packages
   separate, as well as maintaining your own backports or forks.

 * Older package versions can be automatically deleted/rotated, keeping
   repository size manageable whilst allowing downgrades.

 * Packages are automatically GPG signed, improving security as well as
   preventing annoying warnings.

 * No configuring heightweight solutions such as `dak
   <https://wiki.debian.org/DakHowTo>`_ , provisioning a separate HTTP server,
   and stringing together arcane ``dpkg`` commands.


Quick start
-----------

#. Start the server with::

    $ ./aptlyd

#. In another terminal, upload your package::

    $ curl --upload-file my-package.deb http://127.0.0.1:3333/reponame

   ``reponame`` can any arbitrary repository name - if it doesn't exist, APTly
   will automatically create it for you.

    .. tip::

      To upload using curl from a pipe, ensure you use ``--data-binary``::

        $ curl -X PUT --data-binary @- http://127.0.0.1:3333/reponame < my-package.deb

#. Configure your ``sources.list``::

    $ echo 'deb http://127.0.0.1:3333 reponame main' >> /etc/apt/sources.list

#. Save your APTly instance's GPG key::

    $ curl http://127.0.0.1:3333 > /etc/apt/trusted.gpg.d/server.gpg

#. Install your package!

    ::

    $ apt-get update
    $ apt-get install my-package

Creating a new GPG key
----------------------

APTly ships with a dummy key for getting started quickly. To create your own
key, run::

   $ gpg --homedir=/path/to/gpg-home --gen-key
 
Choose all the defaults, making sure not to specify a passphrase.

Uploading multiple files
------------------------

Each upload will refresh the repository from scratch. However, you can save
some processing time for large repos by skipping refreshing the repo until the
end by POSTing to the repo URL::

    for X in *.deb; do
        curl --upload-file ${X} http://127.0.0.1:3333/reponame?refresh_repo=0
    done

    curl -X POST http://127.0.0.1:3333/reponame

Removing versions
-----------------

Versions are automatically rotated, but to manually remove a specific version,
first just locate and remove that file::

   $ rm /path/to/dists/reponame/.../python-bcrypt_0.4-1_amd64.deb

Then refresh that repository::

   $ curl -X POST http://127.0.0.1:3333/reponame

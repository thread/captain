thread-apt-server
=================

Instructions
------------

 $ curl --upload-file my.deb http://127.0.0.1:3333/reponame

For example:

 $ curl --upload-file python-bcrypt_0.4-1_amd64.deb http://127.0.0.1:3333/wheezy-backports

To upload using curl from a pipe, ensure you use --data-binary:

 $ curl -X PUT --data-binary @- http://127.0.0.1:3333/reponame < my.deb

Creating a new key
------------------

 $ gpg --homedir=/path/to/gpg-home --gen-key
 
Choose all the defaults, making sure not to specify a passphrase. Note the
keyid generated.

Client setup
------------

  $ echo 'deb http://127.0.0.1:3333 reponame main' >> /etc/apt/sources.list
  $ curl http://127.0.0.1:3333 > /etc/apt/trusted.gpg.d/server.gpg
  $ apt-get update

Uploading multiple files
------------------------

Each upload will refresh the repo from scratch. However, you can save some
processing time for large repos by skipping refreshing the repo until the end
by POSTing to the repo URL::

  for X in *.deb; do
      curl --upload-file ${X} http://127.0.0.1:3333/reponame?refresh_repo=0
  done

  curl -X POST http://127.0.0.1:3333/reponame

Removing versions
-----------------

Versions are automatically rotated, but to manually remove a version, first
just remove the file:

 $ rm /path/to/dists/reponame/.../python-bcrypt_0.4-1_amd64.deb

Then refresh that repository:

 $ curl -X POST http://127.0.0.1:3333/reponame

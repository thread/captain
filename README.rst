thread-apt-server
=================

Instructions
------------

 $ curl --upload-file my.deb http://server:3333/reponame

For example:

 $ curl --upload-file python-bcrypt_0.4-1_amd64.deb http://server:3333/wheezy-backports

Creating a new key
------------------

 $ gpg --homedir=/path/to/gpg-home --gen-key
 
Choose all the defaults, making sure not to specify a passphrase. Note the
keyid generated.

Client setup
------------

  $ echo 'deb http://server:3333 reponame main' >> /etc/apt/sources.list
  $ curl http://server:3333 > /etc/apt/trusted.gpg.d/thread.gpg
  $ apt-get update

Uploading multiple files
------------------------

Each upload will refresh the repo from scratch. However, you can save some
processing time for large repos by skipping refreshing the repo until the end
by POSTing to the repo URL::

  for X in *.deb; do
      curl --upload-file ${DEB} http://server:3333/myrepo?refresh_repo=0
  done

  curl -X POST http://server:3333/myrepo

thread-apt-server
=================

Instructions
------------

 $ curl --upload-file my.deb http://server:3333/_repo_

For example:

 $ curl --upload-file python-bcrypt_0.4-1_amd64.deb http://server:3333/wheezy-backports

Creating a new key
------------------

 $ gpg --homedir=/path/to/gpg-home --gen-key
 
Choose all the defaults, making sure not to specify a passphrase. Note the
keyid generated.

Client setup
------------

  $ echo 'http://server:3333 _repo_ main' >> /etc/apt/sources.list
  $ curl http://server:3333 > /etc/apt/trusted.gpg.d/thread.gpg
  $ apt-get update

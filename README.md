[io.livecode.ch](http://io.livecode.ch)
===============

[io.livecode.ch](http://io.livecode.ch) is an _early stage prototype_
for turning code repositories into interactive tutorials and books,
with code snippets that can be edited and run on the web.

Test your .io.livecode.ch/_site locally
---------------------------------------

* `git clone https://github.com/namin/io.livecode.ch`
* `cd io.livecode.ch`
* `git submodule init; git submodule update`
* `cd pub/templates/local`
* `git clone https://github.com/<user>/<repo>.git`
* `cd ../..` (back to `pub` directory)
* `python local.py` (powered by [flask](http://flask.pocoo.org/) and [requests](http://docs.python-requests.org/en/latest/))
* visit `http://localhost:5000/learn/<user>/<repo>`
* if you make code changes, refresh the server installation by visiting `http://io.livecode.ch/learn/<user>/<repo>?refresh=1`

Development server-side installation steps
------------------------------------------

* On host machine (skip these steps if you have docker installed directly on your machine, without using [Vagrant](http://www.vagrantup.com/)):
  * `git clone https://github.com/dotcloud/docker.git`
  * `cd docker`
  * Add the following to the end of `Vagrantfile`:


          Vagrant.configure("2") do |config|
            config.vm.network "forwarded_port", guest: 5000, host: 5000
          end


  * `vagrant up`
  * `vagrant ssh`

* On guest machine:
  * `docker pull namin/io.livecode.ch`
  * `sudo apt-get install redis-server python-pip git`
  * `sudo pip install flask redis`
  * `mkdir ~/code`
  * `cd ~/code`
  * `git clone https://github.com/dotcloud/docker-py.git`
  * `cd docker-py`
  * `sudo python setup.py install`
  * `cd ~/code`
  * `git clone https://github.com/namin/io.livecode.ch`
  * `cd io.livecode.ch`
  * `git submodule init; git submodule update`
  * `cd pub`
  * `export APP_SETTINGS=~/code/io.livecode.ch/cfg/vagrant.cfg`
  * `python __init__.py`

Production server-side installation steps
-----------------------------------------

powered by [docker](http://docker.io), [redis](http://redis.io), [flask](http://flask.pocoo.org/)...

* `docker pull namin/io.livecode.ch`
* cd `/var/www`
* `git clone https://github.com/namin/io.livecode.ch`
* `cd io.livecode.ch`
* `git submodule init; git submodule update`
* `cp app.wsgi.sample app.wsgi`
* `sudo cp cfg/apache2-site.sample /etc/apache2/sites-available/io.livecode.ch`
* `sudo a2ensite io.livecode.ch`
* `sudo service apache2 reload`
* `sudo tail -f /var/log/apache2/error.log` (to monitor error logs)

Docker cheat sheet
------------------

* `docker run -i -t -u runner -e HOME=/home/runner namin/io.livecode.ch /bin/bash --login`
   (shell access)
* `docker build -t=namin/dev .`
   (build the image from the [Dockerfile](/Dockerfile))

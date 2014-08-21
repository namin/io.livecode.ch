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

These steps have been tested on an Ubuntu derivative.

* Install dependencies
  * [Install docker](https://docs.docker.com/installation/ubuntulinux/).
  * `sudo apt-get install redis-server python-pip git`
  * `sudo pip install flask redis docker-py`

* Set up local `io.livecode.ch` repository in a directory of your choice
  * `git clone --recursive https://github.com/namin/io.livecode.ch`
  * `export LIVECODE_DIR=``pwd``/io.livecode.ch`

* Install the `io.livecode.ch` docker image
  * Get the official image
    * `docker pull namin/io.livecode.ch`
    * `export LIVECODE_CONFIG="dev"`
  * **Or** build your own from the source repo
    * `cd $LIVECODE_DIR; docker build -t=namin/io.livecode.ch-dev .`
    * `export LIVECODE_CONFIG="dev_docker"`

* Run local development server
  * `export APP_SETTINGS=$LIVECODE_DIR/cfg/$LIVECODE_CONFIG.cfg`
  * `cd $LIVECODE_DIR`
  * `python __init__.py`

Production server-side installation steps
-----------------------------------------

hosted by [DigitalOcean](https://www.digitalocean.com), which also provides many helpful articles:
* [How To Use the DigitalOcean Docker Application](https://www.digitalocean.com/community/articles/how-to-use-the-digitalocean-docker-application)
* [How To Deploy a Flask Application on an Ubuntu VPS](https://www.digitalocean.com/community/articles/how-to-deploy-a-flask-application-on-an-ubuntu-vps)

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

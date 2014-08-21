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

These steps have been tested on a [DigitalOcean](https://www.digitalocean.com) docker application droplet, and work regardless of the actual (sub)domain name of your server (i.e. no need to change occurrences of `io.livecode.ch` in config files).

* [Create a new droplet in the DigitalOcean UI](https://cloud.digitalocean.com/droplets/new):
  * for the image, select the `Applications` tab, then `Docker ... on Ubuntu`:
    ![screenshot of selecting docker application image](https://assets.digitalocean.com/articles/docker/88cIxF8.png)
  * for the other options, select as you please. My options:
    * for the size, I use the second smallest droplet, though any other including the smallest should work too.
    * for the last settings, I keep the default VirtIO enabled (I have not tested it disabled).
      I also like to enable Backups, though it's not essential.

* Initial setup of the server
  * `$ME` refers to your preferred username (e.g. `namin` for me)
  * `$DKR` refers to a docker-enabled user (e.g. `dkr`, which I use for scheduling docker cleanups)
  * as `root`:
    * be sure to set `$ME` and `$DKR` as you like. I do:
      * `export ME=namin`
      * `export DKR=dkr`
    * `apt-get update`
    * `apt-get upgrade`
    * `apt-get install lxc-docker`
    * `adduser $ME` 
    * `usermod -a -G www-data,docker,sudo $ME`
    * `usermod -a -G docker www-data`
    * `adduser $DKR`
    * `usermod -a -G docker $DKR`
  * as `$ME`:
    * set up your favorite editor (and other tools) as you please. I do:
      * set up emacs
        * `sudo apt-get install emacs24`
        * `git clone -b server https://github.com/namin/.emacs.d.git`
           
           (in $HOME directory)
        * run `emacs` to ensure customization works
      * configure git
        * `git config --global user.name "Nada Amin"`
        * `git config --global user.email "namin@alum.mit.edu"`
        * `git config --global core.editor emacs`
    * pull official `io.livecode.ch` docker image
      * `docker pull namin/io.livecode.ch` 
    * set up NGINX
      * `sudo apt-get install nginx`
      * `sudo rm /etc/nginx/sites-enabled/default`
        
        (rationale: the default kicks in too easily)
    * set up dependencies
      * `sudo apt-get install uwsgi uwsgi-plugin-python`
      * `sudo apt-get install redis-server`
      * `sudo apt-get install python-pip python-dev`
      * `sudo pip install flask redis docker-py`
    * set up website
      * `cd /var`
      * `sudo mkdir www`
      * `sudo chown www-data:www-data www`
      * `sudo chmod g+w www`
      * `cd www`
      * `git clone https://github.com/namin/io.livecode.ch.git`
      * `cd io.livecode.ch`
      * `git submodule init; git submodule update`
      * `cp app.wsgi.sample app.wsgi`
      * `cd cfg`
      * `sudo cp nginx-site.sample /etc/nginx/sites-available/io.livecode.ch`
      * `sudo ln -s /etc/nginx/sites-available/io.livecode.ch /etc/nginx/sites-enabled/io.livecode.ch`
      * `sudo cp uwsgi-app.ini.sample /etc/uwsgi/apps-available/io.livecode.ch.ini`
      * `sudo ln -s /etc/uwsgi/apps-available/io.livecode.ch.ini /etc/uwsgi/apps-enabled/io.livecode.ch.ini`
  * as `$DKR`:
    * `mkdir log`
    * `touch log/clean.log`
    * `contrab -e`
    * add line
      * `*/10 * * * * (/var/www/io.livecode.ch/bin/clean) >>log/clean.log`


Docker cheat sheet
------------------

* `docker run -i -t -u runner -e HOME=/home/runner namin/io.livecode.ch /bin/bash --login`
   
   (shell access)

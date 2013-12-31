# namin/io.livecode.ch

FROM ubuntu
MAINTAINER Nada Amin, namin@alum.mit.edu

RUN apt-get install -y python-software-properties
RUN apt-get install -y software-properties-common

RUN add-apt-repository "deb http://archive.ubuntu.com/ubuntu $(lsb_release -sc) main universe restricted multiverse"

RUN apt-get update
RUN apt-get upgrade -y
RUN locale-gen en_US en_US.UTF-8

RUN apt-get install -y curl wget
RUN apt-get install -y git subversion
RUN apt-get install -y unzip
RUN apt-get install -y sed gawk

RUN mkdir /code

# NOTE(namin): I disabled some installations from source, because they get killed.

### Scheme ###
#
RUN apt-get install -y build-essential libtool autoconf libgmp-dev texinfo
# --- killed ---
# RUN cd /code;\
#     git clone https://github.com/marcomaggi/vicare.git;\
#     cd vicare;\
#     sh autogen.sh;\
#     mkdir build;\
#     cd build;\
#     ../configure --enable-maintainer-mode;\
#     make;\
#    make install
#
#### Install from binary ####
RUN cd /code;\
    mkdir vicare;\
    cd vicare;\
    wget -nv http://lampwww.epfl.ch/~amin/dkr/vicare/vicare;\
    wget -nv http://lampwww.epfl.ch/~amin/dkr/vicare/vicare-lib.zip;\
    unzip vicare-lib.zip -d /usr/local/lib/;\
    chmod 755 vicare;\
    cp vicare /usr/local/bin/

### ML ###
RUN apt-get install -y mlton-compiler

### Twelf ###
# --- killed ---
# RUN cd /code;\
#     git clone https://github.com/standardml/twelf.git;\
#     cd twelf;\
#     make mlton;\
#     make install
#
#### Install from binary ####
RUN  cd /code;\
     mkdir twelf;\
     wget -nv http://lampwww.epfl.ch/~amin/dkr/twelf/twelf-server;\
     chmod 755 twelf-server;\
     cp twelf-server /usr/local/bin

### JVM ###
RUN apt-get install -y openjdk-6-jdk

RUN useradd runner -m -d /home/runner -s /bin/bash

RUN apt-get install -y sudo

## From now on, everything is executed as user runner ##
ENV HOME /home/runner
RUN env

RUN sudo -u runner mkdir /home/runner/bin

### Scala / SBT ###
RUN cd /home/runner/bin;\
    sudo -u runner wget -nv http://repo.typesafe.com/typesafe/ivy-releases/org.scala-sbt/sbt-launch/0.13.1/sbt-launch.jar;\
    sudo -u runner echo 'SBT_OPTS="-Xms512M -Xmx1536M -Xss1M -XX:+CMSClassUnloadingEnabled -XX:MaxPermSize=256M"; java $SBT_OPTS -jar `dirname $0`/sbt-launch.jar "$@"' | sudo -u runner tee sbt;\
    sudo -u runner chmod 755 sbt;\
    cd /tmp;\
    sudo -u runner /home/runner/bin/sbt

### Clojure / Leiningen ###
RUN cd /home/runner/bin;\
    sudo -u runner wget -nv https://raw.github.com/technomancy/leiningen/stable/bin/lein;\
    chmod 755 lein;\
    cd /tmp;\
    sudo -u runner /home/runner/bin/lein

## Install io.livecode.ch scripts ##
ADD dkr/livecode-install /tmp/livecode-install
ADD dkr/livecode-run /tmp/livecode-run
RUN cd /home/runner/bin;\
    sudo -u runner cp /tmp/livecode-install .;\
    sudo -u runner cp /tmp/livecode-run .
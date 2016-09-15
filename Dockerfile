# namin/io.livecode.ch

FROM ubuntu:14.04
MAINTAINER Nada Amin, namin@alum.mit.edu

RUN \
  sed -i 's/# \(.*multiverse$\)/\1/g' /etc/apt/sources.list && \
  apt-get update && \
  apt-get -y upgrade && \
  apt-get install -y build-essential && \
  apt-get install -y software-properties-common

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

### SCMUTILS ###
RUN cd /code;\
    mkdir scmutils;\
    cd scmutils;\
    wget -nv http://groups.csail.mit.edu/mac/users/gjs/6946/scmutils-tarballs/scmutils-20130901-x86-64-gnu-linux.tar.gz;\
    cd /usr/local;\
    tar -xvf /code/scmutils/scmutils-20130901-x86-64-gnu-linux.tar.gz
ADD dkr/software/mechanics-shell /usr/local/bin/mechanics-shell

## Java ##
# RUN apt-get install -y openjdk-7-jdk
RUN add-apt-repository -y ppa:webupd8team/java
RUN apt-get update

RUN echo oracle-java6-installer shared/accepted-oracle-license-v1-1 select true | debconf-set-selections && apt-get install -y oracle-java8-installer

RUN echo oracle-java7-installer shared/accepted-oracle-license-v1-1 select true | debconf-set-selections && apt-get install -y oracle-java7-installer

RUN echo oracle-java8-installer shared/accepted-oracle-license-v1-1 select true | debconf-set-selections && apt-get install -y oracle-java8-installer

RUN echo oracle-java9-installer shared/accepted-oracle-license-v1-1 select true | debconf-set-selections && apt-get install -y oracle-java9-installer

## Scala ##
RUN apt-get install -y scala

RUN  cd /code;\
     wget -nv http://downloads.lightbend.com/scala/2.11.8/scala-2.11.8.tgz;\
     tar -xzvf scala-2.11.8.tgz

## user runner ##

RUN apt-get install -y sudo

RUN apt-get install -y dos2unix

RUN useradd -m -d /home/runner -s /bin/bash runner

## Install io.livecode.ch scripts ##
ADD dkr/livecode-install /usr/local/bin/livecode-install
ADD dkr/livecode-run /usr/local/bin/livecode-run

## From now on, everything is executed as user runner ##
ENV HOME /home/runner
RUN env

RUN sudo -u runner mkdir /home/runner/bin
RUN sudo -u runner mkdir /home/runner/files
# namin/io.livecode.ch

FROM ubuntu:18.04
MAINTAINER Nada Amin, namin@alum.mit.edu

RUN \
  sed -i 's/# \(.*multiverse$\)/\1/g' /etc/apt/sources.list && \
  apt-get update && \
  apt-get -y upgrade && \
  apt-get install -y build-essential && \
  apt-get install -y software-properties-common

RUN apt-get install locales
RUN locale-gen en_US en_US.UTF-8

ENV TZ=America/New_York
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone
RUN apt-get update

RUN apt-get install -y curl wget
RUN apt-get install -y git subversion
RUN apt-get install -y unzip
RUN apt-get install -y sed gawk

RUN mkdir /code

# NOTE(namin): I disabled some installations from source, because they get killed.

### Scheme ###
### Vicare ###
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
### Chez ###
RUN apt-get install -y libncurses-dev ncurses-dev libx11-dev
# RUN cd /code;\
#    wget -nv http://github.com/cisco/ChezScheme/archive/v9.4.zip;\
#    unzip v9.4.zip -d .;\
#    cd ChezScheme-9.4;\
#    ./configure;\
#    make install
#### Install from binary ####
#RUN cd /usr/local/bin;\
#    wget -nv http://lampwww.epfl.ch/~amin/dkr/chez/scheme;\
#    chmod 755 scheme;\
#    cd /usr/local/lib;\
#    mkdir -p csv9.4/a6le;\
#    cd csv9.4/a6le;\
#    wget -nv http://lampwww.epfl.ch/~amin/dkr/chez/petite.boot;\
#    wget -nv http://lampwww.epfl.ch/~amin/dkr/chez/scheme.boot

RUN apt-get install -y chezscheme

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
    wget -nv http://groups.csail.mit.edu/mac/users/gjs/6946/scmutils-tarballs/scmutils-20160827-x86-64-gnu-linux.tar.gz;\
    cd /usr/local;\
    tar -xvf /code/scmutils/scmutils-20160827-x86-64-gnu-linux.tar.gz
ADD dkr/software/mechanics-shell /usr/local/bin/mechanics-shell

## Java ##
#RUN apt-get install -y openjdk-6-jdk
#RUN apt-get install -y openjdk-7-jdk
RUN apt-get install -y openjdk-8-jdk
#RUN apt-get install -y openjdk-9-jdk
#RUN apt-get install -y openjdk-10-jdk
RUN apt-get install -y openjdk-11-jdk

#RUN add-apt-repository -y ppa:webupd8team/java
#RUN apt-get update

#RUN echo "oracle-java6-installer shared/accepted-oracle-license-v1-1 select true" | debconf-set-selections;\
#    echo "oracle-java6-installer shared/accepted-oracle-license-v1-1 seen true" | debconf-set-selections;\
#    apt-get install -y oracle-java6-installer

#RUN echo "oracle-java7-installer shared/accepted-oracle-license-v1-1 select true" | debconf-set-selections
#RUN echo "oracle-java7-installer shared/accepted-oracle-license-v1-1 seen true" | debconf-set-selections
#RUN apt-get install -y oracle-java7-installer

#RUN echo oracle-java8-installer shared/accepted-oracle-license-v1-1 select true | debconf-set-selections && apt-get install -y oracle-java8-installer

#RUN echo oracle-java9-installer shared/accepted-oracle-license-v1-1 select true | debconf-set-selections && apt-get install -y oracle-java9-installer

#RUN add-apt-repository -y ppa:linuxuprising/java
#RUN apt update
#RUN echo oracle-java11-installer shared/accepted-oracle-license-v1-2 select true | /usr/bin/debconf-set-selections
#RUN apt install -y oracle-java11-installer

## Scala ##
#RUN apt-get install -y scala

RUN  cd /code;\
     wget -nv http://downloads.lightbend.com/scala/2.12.8/scala-2.12.8.tgz;\
     tar -xzvf scala-2.12.8.tgz

RUN  cd /code;\
     wget -nv http://downloads.lightbend.com/scala/2.11.8/scala-2.11.8.tgz;\
     tar -xzvf scala-2.11.8.tgz

#RUN  cd /code;\
#     wget -nv http://scala-lang.org/files/archive/scala-2.9.3.tgz;\
#     tar -xzvf scala-2.9.3.tgz

## LaTeX ##
RUN apt-get install -y texlive-latex-base texlive-latex-extra

## Racket ##

RUN add-apt-repository ppa:plt/racket
RUN apt-get update
RUN apt-get install -y racket

## SMT ##

RUN apt-get install -y z3
RUN apt-get install -y cvc4

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
# namin/io.livecode.ch

FROM ubuntu:22.04
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
#RUN apt-get install -y mlton-compiler
#RUN apt-get install -y mlton

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
RUN apt-get install -y libtinfo5
RUN cd /code; wget -nv https://ftp.gnu.org/gnu/mit-scheme/stable.pkg/12.1/mit-scheme-12.1-x86-64.tar.gz
RUN cd /code; tar xzf mit-scheme-12.1-x86-64.tar.gz
RUN ls /code
RUN cd /code/mit-scheme-12.1/src; ./configure
RUN cd /code/mit-scheme-12.1/src; make
RUN cd /code/mit-scheme-12.1/src; make install

RUN cd /code;\
    wget -nv https://groups.csail.mit.edu/mac/users/gjs/6946/mechanics-system-installation/native-code/scmutils-20230902.tar.gz;\
    tar xzf scmutils-20230902.tar.gz;\
    cd scmutils-20230902;\
    ./install.sh;\
    cp mechanics.sh /usr/local/bin/mechanics-shell
#ADD dkr/software/mechanics-shell /usr/local/bin/mechanics-shell

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

## OCaml ##

RUN apt-get install -y ocaml-nox

## SBCL (Common Lisp) ##

RUN apt-get install -y sbcl

## SBT (Scala) ##

RUN apt-get update
RUN apt-get install apt-transport-https curl gnupg -yqq
RUN echo "deb https://repo.scala-sbt.org/scalasbt/debian all main" | tee /etc/apt/sources.list.d/sbt.list
RUN echo "deb https://repo.scala-sbt.org/scalasbt/debian /" | tee /etc/apt/sources.list.d/sbt_old.list
RUN curl -sL "https://keyserver.ubuntu.com/pks/lookup?op=get&search=0x2EE0EA64E40A89B84B2DF73499E82A75642AC823" | gpg --no-default-keyring --keyring gnupg-ring:/etc/apt/trusted.gpg.d/scalasbt-release.gpg --import
RUN chmod 644 /etc/apt/trusted.gpg.d/scalasbt-release.gpg
RUN apt-get update
RUN apt-get install -y sbt

## Python ##
RUN apt-get update
RUN apt-get install -y python3-pip python3-dev build-essential libssl-dev libffi-dev python3-setuptools python3-venv


## Tweaks ##
# remove local scheme (MIT Scheme) because it's available as mit-scheme and overtakes chez scheme
RUN rm /usr/local/bin/scheme

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
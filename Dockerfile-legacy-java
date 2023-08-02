# namin/io.livecode.ch

FROM ubuntu:12.04
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

## Java ##
RUN apt-get install -y openjdk-6-jdk
RUN apt-get install -y openjdk-7-jdk
#RUN apt-get install -y openjdk-8-jdk
#RUN apt-get install -y openjdk-9-jdk
#RUN apt-get install -y openjdk-10-jdk
#RUN apt-get install -y openjdk-11-jdk

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
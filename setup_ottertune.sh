#!/bin/bash

# client side setup
sudo apt-get update
sudo apt-get install ant git python3-pip python3-dev python3-tk libssl-dev -y
sudo pip3 install --upgrade setuptools -y

sudo pip3 install fabric3 -y

# install java
sudo add-apt-repository ppa:webupd8team/java
sudo apt-get update

# install gradle
sudo add-apt-repository ppa:cwchien/gradle
sudo apt-get update
sudo apt upgrade gradle -y

# install sysbench
curl -s https://packagecloud.io/install/repositories/akopytov/sysbench/script.deb.sh | sudo bash
sudo apt -y install sysbench

# serverside setup
sudo apt-get update
sudo apt-get install git python3-pip python3-dev python-mysqldb python3-tk rabbitmq-server libmysqlclient-dev libssl-dev mysql-server -y
sudo pip3 install --upgrade setuptools -y

# install az cli
curl -sL https://aka.ms/InstallAzureCLIDeb | sudo bash


# install requirements.  Do this last
sudo pip3 install -r ~/ottertune/server/website/requirements.txt

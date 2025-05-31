#!/usr/bin/env bash
apt-get update
apt-get install -y wget gnupg xz-utils libjpeg-dev libxrender1 libfontconfig1
wget https://github.com/wkhtmltopdf/wkhtmltopdf/releases/download/0.12.6/wkhtmltox_0.12.6-1.buster_amd64.deb
dpkg -i wkhtmltox_0.12.6-1.buster_amd64.deb

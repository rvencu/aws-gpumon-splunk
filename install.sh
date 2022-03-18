#!/usr/bin/env bash

# Stop on any error
set -e

apt install -y python3-pip
pip3 install -r requirements.txt

mv gpumon.py /etc/gpumon.py
mv gpumon.service /etc/systemd/system/gpumon.service

systemctl enable --now gpumon

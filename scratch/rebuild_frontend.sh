#!/bin/bash
cd /home/ubuntu/WDesk
docker compose build frontend
docker compose up -d frontend

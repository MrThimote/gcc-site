#!/bin/sh

# Exit on error
set -e

docker-compose build
docker-compose up -d

# Build assets
docker exec -it prologin_gccsite sh -c '
cd assets
npm install
'

docker exec -it prologin_gccsite python prologin/manage.py migrate
docker exec -it prologin_gccsite python prologin/manage.py collectstatic

docker exec -it prologin_gccsite python prologin/manage.py createsuperuser
docker exec -it prologin_gccsite python prologin/manage.py edition create

#!/bin/bash -x
set e
DIR=$(dirname $0)

# This file is necessary for people running windows + cygwin because windows is a bannanas OS and NPM doesn't support it.


echo "Cleaning static files"
rm -rf static/dist && mkdir -p static/dist/js && mkdir -p static/dist/css && mkdir -p static/dist/fonts && mkdir -p static/dist/images

echo "Building crap"
npm --prefix $DIR run build:babel
npm --prefix $DIR run build:js
npm --prefix $DIR run build:css
npm --prefix $DIR run copy:fonts
npm --prefix $DIR run copy:images

echo "optimizing?"
npm --prefix $DIR run optimize

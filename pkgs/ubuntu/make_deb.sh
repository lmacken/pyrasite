#!/bin/bash -x
# gem install fpm
fpm \
    -t deb \
    -s python \
    --python-install-lib /usr/lib/python2.7/dist-packages \
    --no-python-fix-name \
    --architecture all \
    --url http://pyrasite.com \
    --license GPLv3 \
    --maintainer "Luke Macken <lmacken@redhat.com>" \
    --description "Pyrasite lets you inject arbitrary code into running Python processes" \
    --depends gdb \
    .

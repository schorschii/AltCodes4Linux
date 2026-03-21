#!/bin/bash
set -e

BUILDDIR=altcodes4linux

# check root permissions
if [ "$EUID" -ne 0 ] && ! groups | grep -q sudo ; then
	echo "Please run this script as root!"
	#exit 1 # disabled for github workflow. don't know why this check fails here but sudo works.
fi

# cd to working dir
cd "$(dirname "$0")"

# empty / create necessary directories
if [ -d "$BUILDDIR/usr" ]; then
    sudo rm -r $BUILDDIR/usr
fi
sudo mkdir -p $BUILDDIR/usr/bin

# copy files in place
sudo install -D -m 755 ../../altcodes4linux.py -t $BUILDDIR/usr/bin

# set file permissions
sudo chown -R root:root $BUILDDIR

# build deb
sudo dpkg-deb -Zxz --build $BUILDDIR

echo "Build finished"

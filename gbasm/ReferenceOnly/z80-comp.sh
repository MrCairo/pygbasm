#!/bin/bash

rm $1 $1.o
~/development/rgbds/bin/rgbasm -o $1.o $1.z80
~/development/rgbds/bin/rgblink -o $1 $1.o

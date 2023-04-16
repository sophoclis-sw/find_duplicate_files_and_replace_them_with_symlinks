#!/bin/bash

find . -type l | while read link
do 
   target=$(readlink "$link")
   rm -fv "$link"
   cp -v "$target" "$link"
done


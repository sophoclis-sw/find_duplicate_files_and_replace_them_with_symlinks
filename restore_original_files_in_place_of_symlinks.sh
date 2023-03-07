#!/bin/bash

find . -type l | while read link
do 
   target=$(readlink "$link")
   rm "$link"
   cp -v "$target" "$link"
done


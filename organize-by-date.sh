#!/bin/bash
exiftool -d %Y/%Y-%m-%d "-directory<datetimeoriginal" *.JPG
exiftool -d %Y/%Y-%m-%d "-directory<datetimeoriginal" *.AVI
exiftool -d %Y/%Y-%m-%d "-directory<datetimeoriginal" *.NEF

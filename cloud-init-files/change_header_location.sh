#!/bin/sh
OLD="http\:\/\/srm\-dom0\.to\.infn\.it\/CloudInitFiles\/header\.py"
NEW="http\:\/\/one\-master\.to\.infn\.it\/cloud\-init\-files\/header\.py"
for file in `ls cc_*.py`; do
  echo "Modifying file: $file..."
  sed -i -e 's/'$OLD'/'$NEW'/g' $file
done

#!/bin/sh
OLD="http\:\/\/srm\-dom0\.to\.infn\.it\/test\/header\.py"
NEW="http\:\/\/srm\-dom0\.to\.infn\.it\/CloudInitFiles\/header\.py"
for file in `ls cc_*.py`; do
  echo "Modifying file: $file..."
  sed -i -e 's/'$OLD'/'$NEW'/g' $file
done

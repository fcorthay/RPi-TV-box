#!/usr/bin/bash

INDENT='  '

SCRIPT_DIR=`dirname $0`
CONFIGURATION_SCRIPT_DIR="$SCRIPT_DIR/.."
source $CONFIGURATION_SCRIPT_DIR/configuration.bash

echo 'Grabbing:'
start=`date +%s`
for channel in ${CHANNELS_TO_SCAN[@]}; do
  channel_no_underscore=`echo $channel | tr _ ' '`
  echo "$INDENT$channel_no_underscore"
  $SCRIPT_DIR/epg-grab.py $channel
done
end=`date +%s`
echo "done in $(((end-start)/60)) minutes"

echo
for file in $(find $CHANNELS_FILE_DIR -type f -mmin -10 | sort) ; do
 echo ${file##*/}
done

#!/usr/bin/bash

# Base directory
export TV_BASE_DIR='/home/control/Controls/RPi-TV-box'

# TV channels
export CHANNELS_FILE_DIR='/home/control/Public/www'
export SCANNED_CHANNELS_FILE="$CHANNELS_FILE_DIR/channels-scan.txt"
export DVB_CHANNELS_FILE="$CHANNELS_FILE_DIR/channels-dvb.txt"
export CHANNELS_TO_SCAN=(
  'Arte' 'Planete_Plus' '8_Mont_Blanc'
  'RTS_1' 'TF1'
  'TMC'
  '3_Sat'
)

# Recordings
export RECORD_DIR='/media/storage/recordings'

#!/usr/bin/python3
import argparse
import os
import xmltodict
import time
import datetime
import pytz
import psutil

# ------------------------------------------------------------------------------
# constants
#
RECORDING_COMMAND = 'dvbv5-zap'
OVERRUN_MARGIN = 5

INDENT = '  '
SEPARATOR = 80 * '-'

# ------------------------------------------------------------------------------
# command line arguments
#
parser = argparse.ArgumentParser()
                                                           # epg files directory
parser.add_argument(
    '-e', '--epg', default='/home/control/Public/www',
    help = 'the EPG files directory'
)
                                                       # recording schedule file
parser.add_argument(
    '-l', '--schedule', default='schedule.xml',
    help = 'the recordings schedule file'
)
                                                     # recording files directory
parser.add_argument(
    '-d', '--dir', default='/media/storage/recordings',
    help = 'the recordings directory'
)
                                                                # recording file
parser.add_argument(
    '-f', '--file', default='recording.ts',
    help = 'the recordings schedule file'
)
                                                                 # channels file
parser.add_argument(
    '-c', '--channels', default='/home/control/Public/www/channels-dvb.txt',
    help = 'the DVB channels file'
)
                                                                 # tuner adapter
parser.add_argument(
    '-a', '--adapter', default=1,
    help = 'the tuner adapter id'
)
                                                              # main loop period
parser.add_argument(
    '-p', '--period', default=1,
    help = 'the period of the scheduling loop'
)
                                                                     # verbosity
parser.add_argument(
    '-v', '--verbose', action='store_true', dest='verbose',
    help = 'verbose console output'
)
                                                  # parse command line arguments
parser_arguments = parser.parse_args()
epg_files_directory = parser_arguments.epg
schedule_file_spec = parser_arguments.schedule
if os.sep not in schedule_file_spec:
    schedule_file_spec = os.sep.join([epg_files_directory, schedule_file_spec])
recordings_directory = parser_arguments.dir
recording_file_spec = parser_arguments.file
if os.sep not in recording_file_spec:
    recording_file_spec = os.sep.join(
        [recordings_directory, recording_file_spec]
    )
channels_file_spec = parser_arguments.channels
tuner_adapter = int(parser_arguments.adapter)
sampling_period = float(parser_arguments.period)
verbose = parser_arguments.verbose

build_new_timestamp = False

# ==============================================================================
# Internal functions
#

#-------------------------------------------------------------------------------
# XMLTV date string to datetime object
#
def to_datetime(time_string) :
    return(datetime.datetime.strptime(time_string, '%Y%m%d%H%M%S %z'))

#-------------------------------------------------------------------------------
# datetime object to hh:mm:ss
#
def to_string(datetime_object) :
    return(datetime.datetime.strftime(datetime_object, '%Hh%M'))

#-------------------------------------------------------------------------------
# datetime object to hh:mm:ss
#
def to_string_long(datetime_object) :
    return(datetime.datetime.strftime(datetime_object, '%Y%m%d%H%M%S %z'))

#-------------------------------------------------------------------------------
# timestamp for files
#
def time_stamp() :
    return(to_string_long(datetime.datetime.now()).replace(' ', ''))

#-------------------------------------------------------------------------------
# remove old recordings
#
def purge_old_recordings() :
    seconds_per_day = 60*60*24
    if verbose :
        print('Purging old recordings')
                                                 # loop through recordings files
    file_name_start = recording_file_spec.split(os.sep)[-1]
    file_name_start = file_name_start.split('.')[0]
    recordings_directory = os.sep.join(recording_file_spec.split(os.sep)[:-1])
    current_time = time.time()
    for file_name in os.listdir(recordings_directory) :
        file_spec = os.sep.join([recordings_directory, file_name])
        if os.path.isfile(file_spec) :
            if file_name.startswith(file_name_start) :
                file_time = os.stat(file_spec).st_mtime
                if file_time < current_time - seconds_per_day :
                    if verbose :
                        print(INDENT + file_name)
                    os.remove(file_spec)

#-------------------------------------------------------------------------------
# check if command is running
#
def is_running(command) :

    is_found = False
    pid_list = psutil.pids()
    for pid in pid_list :
        try :
            process_command = psutil.Process(pid).cmdline()
        except :
            process_command = []  # process has ended in between
        if len(process_command) > 0 :
            if process_command[0] == command :
                is_found = True

    return(is_found)

#-------------------------------------------------------------------------------
# find next recording start
#
def next_recording(schedule) :

    next_recording_start = datetime.datetime.now() + datetime.timedelta(days=10)
    next_recording_start = next_recording_start.replace(tzinfo=pytz.UTC)
    if isinstance(schedule, list) :
        for recording in schedule :
            start = to_datetime(recording['start'])
            if start < next_recording_start :
                next_recording_start = start
                next_recording_stop = to_datetime(recording['stop'])
                next_recording_channel = recording['channel']
                next_recording_title = recording['title']
    else :  # last element of list is only the dict
        next_recording_start = to_datetime(schedule['stop'])
        next_recording_stop = to_datetime(schedule['stop'])
        next_recording_channel = schedule['channel']
        next_recording_title = schedule['title']

    return(
        next_recording_start, next_recording_stop,
        next_recording_channel, next_recording_title
    )

#-------------------------------------------------------------------------------
# start recording
#
def start_recording(channel, duration) :
                                                    # add timestamp to file spec
    file_parts = recording_file_spec.split('.')
    file_name = '.'.join(file_parts[:-1])
    file_extension = file_parts[-1]
    output_file_spec = "%s-%s.%s" % (file_name, time_stamp(), file_extension)
    if verbose :
        print(INDENT + output_file_spec)
                                                              # launch recording
    os.system(
        "%s -r '%s' -t %d -o '%s' -c '%s' -a %d >/dev/null 2>&1 &" % (
            RECORDING_COMMAND,
            channel, duration, output_file_spec,
            channels_file_spec, tuner_adapter
        )
    )

    return(output_file_spec)

#-------------------------------------------------------------------------------
# end recording
#
def end_recording(recorded_file_spec, title) :
                                                               # build_file spec
    if build_new_timestamp :
        timestamp = time_stamp()
    else :
        timestamp = recorded_file_spec.split(os.sep)[-1]
        timestamp = timestamp.split('-')[-1]
        timestamp = timestamp.split('.')[0]
    transcoded_file_spec = os.sep.join([
        recordings_directory, "%s-%s.mp4" % (title, timestamp)
    ])
    for charcater in " '" :
        transcoded_file_spec = transcoded_file_spec.replace(charcater, '_')
                                                     # wait for end of recording
    if verbose :
        print(INDENT, end = '')
    record_done = False
    while not record_done :
        record_done = is_running(RECORDING_COMMAND)
        if verbose :
            print('.', end = '')
        time.sleep(1)
    if verbose :
        print()
                                                                # transcode file
    print(INDENT + "transcoding to %s" % transcoded_file_spec)
    os.system(
        "ffmpeg -y -i '%s' -c copy '%s' >/dev/null 2>&1 &" % (
            recorded_file_spec, transcoded_file_spec
        )
    )

# ==============================================================================
# main script
#
                                                    # display working parameters
if verbose :
    print("Controlling recordings")
    print(INDENT + "schedules file      : \"%s\"" % schedule_file_spec)
    print(INDENT + "epg directory       : \"%s\"" % epg_files_directory)
    print(INDENT + "recording directory : \"%s\"" % recordings_directory)
    print(INDENT + "recording file      : \"%s\"" % recording_file_spec)
    print(INDENT + "DVB channels file   : \"%s\"" % channels_file_spec)
    print(INDENT + "tuner adapter id    : %d" % tuner_adapter)
    print(INDENT + "sampling period     : %g sec." % sampling_period)

recording_end = False
state = 'waiting'
old_state = ''
while not recording_end :
    if verbose :
        if state != old_state :
            if old_state in ('waiting', 'recording') :
                print()
            print(state.replace('_', ' '))
            old_state = state
                                                                 # read schedule
    schedule_file = open(schedule_file_spec, 'r')
    schedule_xml = schedule_file.read()
    schedule_file.close()
    schedule_dict = xmltodict.parse(schedule_xml)
                                                    # waiting for next recording
    if state == 'waiting' :
        recording_list = schedule_dict['schedule']['recording']
                                                     # find next recording start
        (next_start, next_stop, channel, title) = next_recording(
            recording_list
        )
        next_event = next_start
        now = datetime.datetime.now(datetime.timezone.utc)
        seconds_to_wait = (next_start - now).total_seconds()
                                                       # remove overrun schedule
        if seconds_to_wait < -OVERRUN_MARGIN :
            if isinstance(recording_list, list) :
                if verbose :
                    print(
                        "removing overrun schedule at %s" %
                            (to_string(next_start))
                    )
                schedule_dict['schedule']['recording'] = [
                    element for element in recording_list
                        if not (element['start'] == to_string_long(next_start))
                ]
                schedule_file = open(schedule_file_spec, 'w')
                schedule_file.write(xmltodict.unparse(schedule_dict, pretty=True))
                schedule_file.close()
            else :
                if verbose :
                    print('end of recodings list')
                recording_end = True
                                                                 # check if done
        elif seconds_to_wait <= sampling_period :
            state = 'starting_recording'
                                                               # start recording
    elif state == 'starting_recording' :
        to_transcode = start_recording(
            channel, (next_stop - now).total_seconds()
        )
        next_event = next_stop
        seconds_to_wait = 0
        state = 'recording'
                                                  # waiting for end of recording
    elif state == 'recording' :
        now = datetime.datetime.now(datetime.timezone.utc)
        seconds_to_wait = (next_stop - now).total_seconds()
        if seconds_to_wait <= sampling_period :
            state = 'stopping_recording'
                                                                # stop recording
    elif state == 'stopping_recording' :
        end_recording(to_transcode, title)
        purge_old_recordings()
        seconds_to_wait = 0
        state = 'waiting'
                                                      # wait for sampling period
    if verbose :
        if seconds_to_wait > 0 :
            now_utc = pytz.utc.localize(datetime.datetime.now())
            print(
                INDENT +
                "waiting from %s to %s (%d sec)" % (
                    to_string(now_utc), to_string(next_event), seconds_to_wait
                ) +
                10*' ',
                end = "\r"
            )
    time.sleep(sampling_period)

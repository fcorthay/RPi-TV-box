#!/usr/bin/python3
import argparse
import os
import xmltodict
from datetime import datetime

# ------------------------------------------------------------------------------
# constants
#
EPG_FILES_DIR = ''

INDENT = '  '
SEPARATOR = 80 * '-'

# ------------------------------------------------------------------------------
# command line arguments
#
parser = argparse.ArgumentParser()
                                                                       # channel
parser.add_argument(
    'channel', default='Arte', nargs='?',
    help = 'channel name'
)
                                                           # epg files directory
parser.add_argument(
    '-d', '--dir', default='/home/control/Public/www',
    help = 'the DVB channels list file'
)
                                                                     # verbosity
parser.add_argument(
    '-v', '--verbose', action='store_true', dest='verbose',
    help = 'verbose console output'
)
                                                  # parse command line arguments
parser_arguments = parser.parse_args()
channel_name = parser_arguments.channel
epg_files_directory = parser_arguments.dir
verbose = parser_arguments.verbose

# ==============================================================================
# Internal functions
#

#-------------------------------------------------------------------------------
# Read programes from EPG XML
#
def read_epg(time_string) :
                                                            # read EPG from file
    epg_file = open(epg_file_spec, 'r')
    epg_xml = epg_file.read()
    epg_file.close()
    epg_dict = xmltodict.parse(epg_xml)
                                                           # retreive programmes
    programmes = epg_dict['tv']['programme']

    return(programmes)

#-------------------------------------------------------------------------------
# EPG time string to datetime
#
def to_datetime(time_string) :
                                                             # remove UTC offset
    (local_time, UTC_offset) = time_string.split(' ')
                                                           # convert to datetime
    local_time = datetime.strptime(local_time, '%Y%m%d%H%M%S')

    return(local_time)

#-------------------------------------------------------------------------------
# Sort programme by time
#
def sort_programmes(programmes) :
                                                              # sort start times
    start_times = []
    for programme in programmes :
        start_time = programme['@start']
        start_time = start_time.split(' ')[0]
        start_times.append(start_time)
    start_times = sorted(start_times)
                                                        # build sorted programme
    sorted_programmes = []
    for start_time in start_times :
        for programme in programmes :
            if start_time in programme['@start'] :
                sorted_programmes.append(programme)

    return(sorted_programmes)

#-------------------------------------------------------------------------------
# Print programmes schedules and titles
#
def print_epg(programmes) :
                                                           # retreive programmes
    for programme in programmes :
        start_time = to_datetime(programme['@start'])
        start_time_string = start_time.strftime('%d %b %H:%M')
        end_time = to_datetime(programme['@stop'])
        end_time_string = end_time.strftime('%H:%M')
        duration = end_time - start_time
        duration_string = ("%s" % duration)[:-3]
        print(
            "%s - %s (%s)"
                % (start_time_string, end_time_string, duration_string)
        )
        print(INDENT + programme['title']['#text'])

# ==============================================================================
# main script
#
epg_file_spec = os.sep.join(
    [epg_files_directory, channel_name.replace(' ', '_') + '.xml']
)
                                                    # display working parameters
if verbose :
    print("Creating EPG display for \"%s\"" % channel_name)
    print(INDENT + "epg file : \"%s\"" % epg_file_spec)
    print()
                                                           # retreive programmes
programmes = sort_programmes(read_epg(epg_file_spec))
if verbose :
    print_epg(programmes)

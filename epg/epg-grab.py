#!/usr/bin/python3
import argparse
import os
import xmltodict

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
                                                            # channels list file
parser.add_argument(
    '-c', '--channels', default='',
    help = 'the DVB channels list file'
)
                                                                   # output file
parser.add_argument(
    '-o', '--output', default='/tmp/epg.xml',
    help = 'the grabbed EPG file'
)
                                                                      # log file
parser.add_argument(
    '-l', '--logFile', default='/tmp/epg-grab.log',
    help = 'the commands log file'
)
                                                                   # tuner demux
parser.add_argument(
    '-D', '--demux', default='/dev/dvb/adapter0/demux0',
    help = 'the tuner demux'
)
                                                                     # verbosity
parser.add_argument(
    '-v', '--verbose', action='store_true', dest='verbose',
    help = 'verbose console output'
)
                                                  # parse command line arguments
parser_arguments = parser.parse_args()
channel = parser_arguments.channel
epg_files_directory = parser_arguments.dir
channels_list_file_spec = parser_arguments.channels
if channels_list_file_spec == '' :
    channels_list_file_spec = os.sep.join(
        [epg_files_directory, 'channels-dvb.txt']
    )
epg_file_spec = parser_arguments.output
log_file_spec = parser_arguments.logFile
tuner_demux = parser_arguments.demux
verbose = parser_arguments.verbose

acquire_again = True

# ==============================================================================
# Internal functions
#

#-------------------------------------------------------------------------------
# Start DVB tuner
#
def start_tuner() :
                                                               # execute command
    channel_with_spaces = channel.replace('_', ' ')
    os.system(
        "dvbv5-zap -c %s -r \"%s\" >%s 2>&1 &" %
            (channels_list_file_spec, channel_with_spaces, log_file_spec)
    )

#-------------------------------------------------------------------------------
# Launch grabber
#
def grab_EPG() :
                                                               # execute command
    os.system(
        "epgrab -i %s >%s 2>%s" % (tuner_demux, epg_file_spec, log_file_spec)
    )

#-------------------------------------------------------------------------------
# Stop DVB tuner
#
def stop_tuner() :
                                                               # execute command
    os.system('pkill dvbv5-zap')

#-------------------------------------------------------------------------------
# Demultiplex program guides
#
def demultiplex_program_guides() :
                                                            # read EPG from file
    epg_file = open(epg_file_spec, 'r')
    epg_xml = epg_file.read()
    epg_file.close()
    epg_dict = xmltodict.parse(epg_xml)
                                                                 # find channels
    channels_list_file = open(channels_list_file_spec, 'r')
    channel_ids = {}
    channel_name = ''
    for line in channels_list_file :
        if line.startswith('[') :
            channel_name = line[1:line.find(']')]
        if 'SERVICE_ID' in line :
            service_id = line.split('=')[1].strip()
            channel_ids[service_id] = channel_name
    channels_list_file.close()
                                                                 # find channels
    programmes = epg_dict['tv']['programme']
    grabbed_channels = {}
    for programme in programmes :
        channel_id = programme['@channel'].split('.')[0]
        grabbed_channels[channel_id] = channel_ids[channel_id]
    if verbose :
        print('Found channels:')
        for (channel_id, channel_name) in grabbed_channels.items() :
            print(INDENT + "%s : %s" % (channel_id, channel_name))
                                               # write individual program guides
    if verbose :
        print('Writing EPG files:')
    for (channel_id, channel_name) in grabbed_channels.items() :
                                                             # prepare file spec
        no_space_channel_name = channel_name.replace(' ', '_')
        channel_epg_file_spec = os.sep.join(
            [epg_files_directory, no_space_channel_name + '.xml']
        )
        if verbose :
            print(INDENT + channel_epg_file_spec)
                                                     # separate programmes by id
        channel_programmes = []
        for programme in programmes :
            individual_channel_id = programme['@channel'].split('.')[0]
            if individual_channel_id == channel_id :
                channel_programmes.append(programme)
                channel_programmes[-1]['@channel'] = no_space_channel_name
        programme_dict = {'tv' : {
            '@generator-info-name': 'epg-grab',
            'programme' : channel_programmes
        }}
                                                                   # add doctype
        programme_xml = xmltodict.unparse(programme_dict, pretty=True)
        programme_xml = programme_xml.replace(
            "\n", "\n<!DOCTYPE tv SYSTEM \"xmltv.dtd\">\n", 1
        )
                                                                 # write to file
        channel_epg_file = open(channel_epg_file_spec, 'w')
        channel_epg_file.write(programme_xml)
        channel_epg_file.write("\n")
        channel_epg_file.close()

# ==============================================================================
# main script
#
                                                    # display working parameters
if verbose :
    print("Grabbing EPG for \"%s\"" % channel)
    print(INDENT + "tuner demux        : \"%s\"" % tuner_demux)
    print(INDENT + "channels list file : \"%s\"" % channels_list_file_spec)
    print(INDENT + "output file        : \"%s\"" % epg_file_spec)
    print(INDENT + "log file           : \"%s\"" % log_file_spec)
                                                                   # start tuner
if acquire_again :
    start_tuner()
                                                          # grab programme guide
    grab_EPG()
                                                                    # stop tuner
    stop_tuner()
                                                    # demultiplex program guides
demultiplex_program_guides()

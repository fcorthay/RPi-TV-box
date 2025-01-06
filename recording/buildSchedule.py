#!/usr/bin/python3
import argparse
import os
import xmltodict
import datetime

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
                                                                    # rules file
parser.add_argument(
    'rules', default='ruleSet.xml', nargs='?',
    help = 'rules file'
)
                                                       # recording schedule file
parser.add_argument(
    '-l', '--schedule', default='schedule.xml',
    help = 'the recordings schedule file'
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
script_dir = os.path.dirname(os.path.realpath(__file__))
parser_arguments = parser.parse_args()
rules_file_spec = os.sep.join([script_dir, parser_arguments.rules])
schedule_file_spec = parser_arguments.schedule
epg_files_directory = parser_arguments.dir
verbose = parser_arguments.verbose

acquire_again = True

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
def to_time(datetime_object) :
    return(datetime.datetime.strftime(datetime_object, '%Hh%M'))

#-------------------------------------------------------------------------------
# Check if a rule matches
#
def rule_matches(rule, channel, title) :
                                                                 # check channel
    channel_matches = False
    if 'channel' in rule :
        if rule['channel']['@name'] == channel :
            channel_matches = True
    else :
        channel_matches = True
                                                                 # check title
    title_matches = False
    if 'title' in rule :
        rule_title = rule['title']
        if '@is' in rule_title:
            if rule_title['@is'] == title :
                title_matches = True
        if '@contains' in rule_title:
            if rule_title['@contains'] in title :
                title_matches = True

    return(channel_matches and title_matches)

#-------------------------------------------------------------------------------
# Build a list of programmes based on the rule set
#
def build_programme_list() :
                                                          # read rules from file
    rules_file = open(rules_file_spec, 'r')
    rules_xml = rules_file.read()
    rules_file.close()
    rules_dict = xmltodict.parse(rules_xml)
                                                          # build EPG files list
    files_list = []
    for file in os.listdir(epg_files_directory):
        if file.endswith(".xml"):
            epg_file_spec = os.path.join(epg_files_directory, file)
            with open(epg_file_spec, 'r') as file:
                last_line = file.read().splitlines()[-1]
            if last_line == '</tv>' :
                files_list.append(epg_file_spec)
                                                         # build programmes list
    programmes = []
    for epg_file_spec in files_list :
        epg_file = open(epg_file_spec, 'r')
        epg_xml = epg_file.read()
        epg_file.close()
        epg_dict = xmltodict.parse(epg_xml)
        programmes += epg_dict['tv']['programme']
                                                            # loop through rules
    if verbose :
        print()
        print('Checking rules')
    matches = []
    for rule in rules_dict['ruleSet']['rule'] :
        if verbose :
            print("\n")
            print(rule)
        for programme in programmes :
            channel = programme['@channel']
            title = programme['title']['#text']
            if rule_matches(rule, channel, title) :
                matches.append(programme)
                if verbose :
                    print()
                    print(programme)

    return(matches)

#-------------------------------------------------------------------------------
# Build a schedule based on the recordings list
#
def build_schedule(programmes) :
    schedule = []
    if verbose :
        print()
        print('Building schedule')
                                                       # loop through programmes
    for programme in programmes :
        channel = programme['@channel']
        title = programme['title']['#text']
        start = to_datetime(programme['@start'])
        stop = to_datetime(programme['@stop'])
                                                    # check if time slot is free
        time_slot_is_free = True
        for occupied in schedule :
            if (start < occupied['stop']) and (stop > occupied['start']) :
                time_slot_is_free = False
        if time_slot_is_free :
            if verbose :
                print(INDENT + "%s - %s : %s" %
                    (to_time(start), to_time(stop), title)
                )
            schedule.append({
                'start' : start,
                'stop' : stop,
                'channel' : channel,
                'title' : title
            })
        else :
            if verbose :
                print(2*INDENT + "slot %s - %s for \"%s\" is occupied" %
                    (to_time(start), to_time(stop), title)
                )
                                                            # sort by start time
    sorting_dict = {}
    for item in schedule :
        epoch = int(item['start'].timestamp())
        sorting_dict[epoch] = item
    sorted_scedule = []
    for key in sorted(sorting_dict.keys()) :
        sorted_scedule.append(sorting_dict[key])

    return(sorted_scedule)

# ==============================================================================
# main script
#
                                                    # display working parameters
if verbose :
    print("Building recording schedule")
    print(INDENT + "rules file     : \"%s\"" % rules_file_spec)
    print(INDENT + "schedules file : \"%s\"" % schedule_file_spec)
    print(INDENT + "epg directory  : \"%s\"" % epg_files_directory)
                                                          # build programme list
to_record = build_programme_list()
                                                                # build schedule
schedule = build_schedule(to_record)
if verbose :
    print()
    print('Schedule:')
    for recording in schedule :
        print(INDENT + "%s - %s : %s, %s" % (
            to_time(recording['start']),
            to_time(recording['stop']),
            recording['channel'],
            recording['title'])
        )

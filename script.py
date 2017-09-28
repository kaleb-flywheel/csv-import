# Import a CSV of subject metadata into Flywheel.
# Each row is a subject, each column is a value. Expecting one subject in each file (i.e. no checking for duplicates). 
# First row must contain header.
# Subject Code matching input column name, or default to "Subject ID"
# To do:
#	get user contenxt and remove Imad's API key
#	Add field type (string, int, etc) to make search facet useful (probably expected in the second row).  
#   Need to implement subject code not in first colum

import os
import sys
import time
import csv
import json
import re

# Gear basics
print 'Setup'
flywheel_base = '/flywheel/v0'
input_folder = os.path.join(flywheel_base, 'input/file')
output_folder = os.path.join(flywheel_base, 'output')
config_file = os.path.join(flywheel_base, 'config.json')

# Grab the input file path
input_filename = os.listdir(input_folder)[0]
input_filepath = os.path.join(input_folder, input_filename)

# Grab config from config.json
print 'Reading config'
with open(config_file) as fp:
    config = json.load(fp)

if 'Match_Column' in config['config']:
    MatchColumn = config['config']['Match_Column'].strip()
else:
    MatchColumn = 'Subject ID'

if 'Group_Tags_By' in config['config']:
    GroupTagsBy = config['config']['Group_Tags_By'].strip()
    if GroupTagsBy != "":
        if not re.match('^[a-zA-Z0-9][a-zA-Z0-9_-]+$', GroupTagsBy):
            print 'Group By Tags is invalid.'
            print 'Valid values are: blank, alphanumeric including dashes and underscores'
            sys.exit(1)
else:
    GroupTagsBy = ""

# published gear -----> fileid = config['inputs']['csv']['hierarchy']['id']
# local testing  -----> fileid = '59c615f74cffa9001ab7385d'

fileid = '59c615f74cffa9001ab7385d'
#fileid = config['inputs']['file']['hierarchy']['id']

# Load Flywheel Python SDK
print 'Loading Python SDK'
from flywheel import Flywheel
fw = Flywheel('dev.flywheel.io:mfi2q5rNrzVAoOzoAt')

# get project information from file
acquisition = fw.get_acquisition(fileid)
session = fw.get_session(acquisition['session'])
project = fw.get_project(session['project'])
projectid = project['_id']
projectname = project['label']

# read CSV into list
print 'Reading in CSV'
with open(input_filepath, 'rb') as f:
    reader = csv.reader(f)
    rows = list(reader)

# Check if matching column exists
if MatchColumn not in rows[0]:
    print("Match Column not found in CSV")
    sys.exit(1)

# make list into json
headers = rows[0]	
csv_subjects = []
for row in rows[1:]:
    newdict = {}
    for i in range(0, len(headers)):
        newdict[headers[i]] = row[i]
    csv_subjects.append(newdict)

# Build the string and update session
print 'Updating sessions'
sessions = fw.get_project_sessions(projectid)

for row in csv_subjects:
    subjectfound = 0
    for session in sessions:
        if session['subject']['code'] == row[MatchColumn]:
            subjectfound += 1
            val = row.copy()
            del val[MatchColumn]
            if GroupTagsBy == "":
                myobject = {'subject': {'info': val}}
            else:
                myobject = {'subject': {'info': {GroupTagsBy: val}}}
            fw.modify_session(session['_id'], myobject)
    if not subjectfound:
        #print "Subject Code %s in %s does not match a subject in the %s project." % (row[MatchColumn], input_filename, projectname)
        print 'Subject Code ' + row[MatchColumn] + ' in ' + input_filename + ' does not match a subject in the ' + projectname + ' project' + '.'

# Add record keeping note to project notes
if not GroupTagsBy:
    fw.add_project_note(projectid, 'Imported %d fields from %s' % ((len(headers) - 1), input_filename) )
    #fw.add_project_note(projectid, 'Imported ' + str(len(headers) - 1) + ' fields from ' + input_filename)
else:
    fw.add_project_note(projectid, 'Imported %d fields from %s, grouped by %s' % ((len(headers) - 1), input_filename, GroupTagsBy))
    #fw.add_project_note(projectid, 'Imported ' + str(len(headers) - 1) + ' fields from ' + input_filename + ', grouped by ' + GroupTagsBy)

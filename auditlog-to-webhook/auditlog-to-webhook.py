#!/usr/local/filewave/python/bin/python

# reads the last x lines of the audit.log and POSTS them as a json to webhook_url, wrapped in message_template. 
# tries to avoid posting the same message twice by saving the last processed line to lastlinefile
# allows for skipping entire lines via bannedlines , and removing parts of lines via remove_these_parts
# cglattfelder, may 2021

webhook_url = 'https://chat.googleapis.com/v1/'  

message_template = {'text':''}

auditlog='/usr/local/filewave/log/audit.log'
lastlinefile='/root/auditlog-to-webhook/lastline-processed.txt'
pidfile='/root/auditlog-to-webhook/script.pid'

pause_between_lines=1 # in seconds

debug=True
send=True

sizetoread=50000   # read the last x characters in the file at every run

bannedlines = ['\'type\': \'ActiveDirectory\'}]\' - SUCCESS',
  'Schedule LDAP custom field extraction - SUCCESS',
  'logged on - SUCCESS','User logged out - SUCCESS',
  'VPP incremental sync - ','is already logged on - ERROR: HTTP 409',
  'Fetching Personal Recovery Key information - ERROR: No FileVault2Device matches the given query',
  'admin name: \'fwadmin\' Save Edited Custom Fields Values - SUCCESS'
]  #any line containing the strings above will not be posted. 

remove_these_parts = ['adminKeyValue:.+,']  #replace empty spaces/values with .+ ; i.e. to replace Argh(anything): use Argh.+:

### no changes should be required after this line

import json
import requests
import re
import sys
import time
import os


def check_pid(pid):        
    """ Check For the existence of a unix pid. """
    try:
        os.kill(pid, 0)
    except OSError:
        return False
    else:
        return True

# simple locking with a file containing a pid. 
if os.path.isfile(pidfile):
  with open(pidfile, 'r') as f:
    otherpid=f.read()
    if otherpid is not None:
      if check_pid(int(otherpid)):
        print('found active running process - exiting')
        sys.exit(0)

me=os.getpid()
with open(pidfile, 'w') as ff:
  ff.write(str(me))


def vprint(schtring):
  if debug: print(schtring)

def post(message):
  r_headers = {'Content-Type': 'application/json; charset=UTF-8'}
  m = message_template
  m['text'] = message.rstrip()
  vprint(m)
  if send:
    resp = requests.post( webhook_url , headers=r_headers , data = json.dumps(m) )
    vprint(resp)

# read the audit logs last x bytes as defined by sizetoread
with open(auditlog,'r') as f:
  f.seek(0,2)
  size=f.tell()
  f.seek(max(size-sizetoread,0),0)
  f.readline() # to ditch the first, most probably incomplete line
  lin = f.readlines()

content = lin

# if we've run before, chances are we don't need to process everything all over. let's avoid posting twice
i=0
try:
  with open(lastlinefile,'r') as f:
    last=f.readline()
  vprint("previous last line found: %s " % last)
  if content[-1] == last: 
    vprint('nothing new under the sun')
    os.remove(pidfile)
    sys.exit(0)
  for l in content:
    if l == last:
      print("lastline found at index %s" % i)
      break
    i+=1
except Exception as e:
  vprint(e)
  pass

if i == len(content): i=-1

# now for the new stuff.
content = lin[i+1:]
print(l)
for l in content:
  lastl=l
  if any(map(l.__contains__, bannedlines)) :            # skip all lines containing a substring mentioned in bannedlines
    vprint("skipping line, contains banned substring")
    continue   
  for exp in remove_these_parts:                        # remove things from lines as mentioned in remove_these_parts
    l = re.sub(exp,'',l) 
  vprint(l)
  post(l)
  time.sleep(pause_between_lines)

if lastl: vprint("last line processed: %s" % lastl)
with open(lastlinefile,'w') as f:
  f.write(lastl)

os.remove(pidfile)

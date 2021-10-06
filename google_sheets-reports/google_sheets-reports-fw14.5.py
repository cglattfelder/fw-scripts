#!/usr/bin/env python3
#script to create a full table of information via API calls to FileWave Web Admin Backend , enriched with custom field inventory information

# data source - filewave server address, and inventory token. 
secrets_file='/root/complete-report/secrets.json'  # json file containing server_name,server_token values
gspread_token_file='/root/complete-report/token.json'

# sanity check on config files
import sys
import json
try:
  with open(secrets_file) as f:
    d=json.load(f)
    server_name=d['server_name']
    server_token=d['server_token']
except Exception as e:
  print("Issue %s when trying to access configuration file ; please fix and retry")
  sys.exit(1)

# google sheets information
gsheets_document_name='fiwa-m-autoexport'
gsheets_sheet_name='Clients'

# Header line
import datetime
headerline=["Automatic","export", "from:", server_name , "", "", "last updated:", "%s" % datetime.datetime.now() ]
headerline2=["usage:","","","",'"=IMPORTRANGE("https://docs.google.com/spreadsheets/d/path-to-your-sheets-docment"; "Clients!A1:Z1000")"']

# values to report from basic client data , in order of output - very last column is always the group path to the original client . 
# choose from : 'id', 'location' ( path to client ), 'name', 'comment', 'parent_id', 'type', 'flags', 'management_mode', 'date_created', 'date_modified', 'serial_or_mac', 'state'
client_columns = [ 'id' , 'name' , 'serial_or_mac', 'comment', 'date_created', 'date_modified', 'location' ]  

# built in inventory fields , in order 
inventory_fields_columns = [ 'last_ldap_username', 'auth_username' , 'enroll_date', 'free_disk_space', 'current_ip_address','filewave_client_locked','state','OperatingSystem:build','OperatingSystem:name'  ]

# custom field values to report , in order 
custom_field_columns = [ 'ldap_department','ldap_firstname','ldap_lastname','fw_lastconnect','mac_device_model_2021' ]

# Debug output
DEBUG=True
# Run all extraction code, return results as json, but do not write to google sheets.
DRYRUN=False

###no further modifications required after this line ###

import requests
import sys
import json
from copy import copy
import gspread

from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry

# in case we have a busy server, we have to be sure to retry when getting back errors or "come back later"
retry_strategy = Retry(
    total=3,
    status_forcelist=[429, 500, 502, 503, 504],
    allowed_methods=["HEAD", "GET", "OPTIONS"]
)
adapter = HTTPAdapter(max_retries=retry_strategy)
http = requests.Session()
http.mount("https://", adapter)
http.mount("http://", adapter)

def vprint(schtring):
  if DEBUG: print(schtring)

webadmin_api = 'https://' + server_name + '/api/'
inventory_api = 'https://' + server_name + ':20445/inv/api/v1/'
authheader = {'Authorization': server_token}
postheader = {'Content-Type': 'application/json', 'Authorization': server_token}

# get the tree hierarchy of groups in the system 
# TODO - handling next / limits ? 
try:
  r = requests.get(webadmin_api+'devices/internal/groups', headers=authheader)
  groupstree_data = r.json()['groups_hierarchy']['groups']
except Exception as e:
  print("found issue %s when connecting to server for extraction ; fix token/servername or server and try again please" %e)
  sys.exit(1)

vprint(groupstree_data)
vprint("total number of groups: %s" % len(groupstree_data))

# get a simple groupnames dict going
groupnames={}
for group in groupstree_data:
  groupnames[group['id']] = group['label']

# return a "pretty" path in a format like /test_group/my_new_clients/ for a given parentID
def group_path(group_id):
  for group in groupstree_data:
    if group['id'] == group_id:
      prettypath = ''
      for element in group['path'].split('.'):
         prettypath = prettypath +'/'+ groupnames[int(element)]
      return(prettypath)

#create a list of all users with their groups - i.e the group where their "original" is located.
clients = {}
uctr=0
for group in groupstree_data:  # as long as there's a 'next' URL, keep fetching more results, and append results to 'rows' 
  # skip clones, and smart groups
  if group['group_type'] != "standard" : continue
  if group['is_clone'] == True : continue
  try:
    r = http.get(webadmin_api + 'devices/v1/devices?parent_id=%s' % group['id'], headers=authheader)
    resp=r.json()
    rows=resp['results']['rows']
    next_page=resp['next']
    while next_page != None:
      r2 = http.get(next_page, headers=authheader)
      resp2=r2.json()
      rows = rows + resp2['results']['rows']
      next_page=resp2['next']
    vprint("resp: %s" % resp['next'])
  except Exception as e:
    vprint("issue getting group memberships :%s" % e)
    pass

  for hit in rows: # processing the data we got back. 
    if hit['type'] == 'user':  #once we find a record type "user" , we collect data in the order described by configuration above.
      uctr+=1
      vprint("found user nr %s : %s" % (uctr,hit)) 
      newclient = []
      for item in client_columns:
        if item == 'location': 
          newclient.append(group_path(hit['parent_id']))
        else:
          newclient.append(hit[item])      
      clients[newclient[0]] = newclient[1:]

vprint("total number of clients: %s" % len(clients.keys()))

# build a query for listed custom fields , send it , and enrich client list with it . 

querytemplate = {"criteria":{"expressions":[{"column":"filewave_id","component":"Client","operator":"is_not","qualifier":0}],"logic":"all"},"fields":[],"main_component":"Client","version":3}
inventory_fields_template = [{"column":"filewave_id","component":"Client"}]
custom_fields_template = [{"column":"my_custom_field","component":"CustomFields"}]

# parameterise the query with the fields requested according to configuration

# inject all custom fields here
custom_fields = []
for field in custom_field_columns:
  parameterised_template = copy(custom_fields_template)
  parameterised_template[0]['column'] = field
  custom_fields.append(copy(parameterised_template[0]))

# inject all inventory fields here
inventory_fields = []
for field in inventory_fields_columns:
  parameterised_template = copy(inventory_fields_template)
  if ':' in field:
    componentname,fieldname=field.split(':')
    parameterised_template[0]['component'] = componentname
  else:
    fieldname=field
  parameterised_template[0]['column'] = fieldname
  inventory_fields.append(copy(parameterised_template[0]))

# assemble into query
queryheader = [{"column":"filewave_id", "component":"Client"}]
querytemplate['fields'] = queryheader + inventory_fields + custom_fields

vprint("inventory query: " + json.dumps(querytemplate))

# run the query
r = requests.post(inventory_api + 'query_result/',data=json.dumps(querytemplate), headers=postheader)
custom_fields = r.json()

if 'values' not in custom_fields:
  print("Inventory Query provided no results; aborting. Details follow:")
  print(r.text)
  print(custom_fields)
  sys.exit(0)

vprint("total number of inventory clients: %s" % len(custom_fields['values']))

# recalulate sizes , and reorganise results in a dictionary for easier processing
custom_field_data = {}

## special field handling - to reformat output.

# if we have free_disk space , inventory returns bytes. so we have to calculate and replace with GB values here. 
sizeposition=0
if 'free_disk_space' in inventory_fields_columns: sizeposition=inventory_fields_columns.index('free_disk_space')   

#if we have state , inventory returns an integer. so we'll have to substitute that ..
stateposition=0
if 'state' in inventory_fields_columns: stateposition=inventory_fields_columns.index('state')
state_dictionary={0:"Tracked",1:"Archived",2:"Missing",3:"Untracked",4:"Disabled"} # from /components endpoint : [[0,"Tracked"],[1,"Archived"],[2,"Missing"],[3,"Untracked"],[4,"Disabled"]

for client in custom_fields['values']:
    custom_field_data[client[0]] = client[1:]
    if sizeposition > 0:
      if custom_field_data[client[0]][sizeposition] is not None:
        custom_field_data[client[0]][sizeposition] = "%s GB" % round(custom_field_data[client[0]][sizeposition] / 1024 / 1024 / 1024,1)
    if stateposition > 0:
      if custom_field_data[client[0]][stateposition] is not None:
        custom_field_data[client[0]][stateposition] = state_dictionary[custom_field_data[client[0]][stateposition]]

# add custom fields values to the clients list 
for client in clients:
  if client in custom_field_data:
    clients[client] = clients[client] + custom_field_data[client]

if DRYRUN:
  print(clients)
  sys.exit(0)

# write to google ; connect first
gc = gspread.service_account(filename=gspread_token_file)
sh = gc.open(gsheets_document_name)
worksheet = sh.worksheet(gsheets_sheet_name)

# prepare list of lists for update call to google sheets. 
listoflists = []
listoflists.append(headerline)
listoflists.append(headerline2)
headerlist = client_columns + inventory_fields_columns + custom_field_columns
listoflists.append(headerlist)

# flatten the data we've got out of filewave
for key,val in clients.items():
  listoflists.append([key] + val)

# clear the existing worklist, and update the data in one API call
worksheet.clear()
worksheet.update('A1',listoflists)

sys.exit(0)

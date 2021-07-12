#!/usr/local/filewave/python/bin/python3
#updates custom field with comment, works only on server locally 
#and only for desktop clients. 
#specify filewave server name as environment variable fw_server
#specify filewave server inventory token as environment variable fw_inv_token 
#specify filewave custom field name as environment variable fw_customfield
# example : fw_server="my.great.server" fw_inv_token="e61298zsjjop15" fw_customfield="fw_comment" /usr/local/filewave/python/bin/python ./comments-to-customfield.py

import requests
import sys
import datetime
import json
import psycopg2
import unicodedata
import os
import time
VERBOSE = False

# input parsing
try:
    fw_token=os.environ['fw_inv_token']
    servername=os.environ['fw_server']
    custom_field_name=os.environ['fw_customfield']
except Exception as e:
    print('missing environment variables %s' % e ) 
    sys.exit(1)

fw_base_url = "https://" + servername + ":20445/"

def vprint(schtring):
    if VERBOSE: print(schtring)

#connect to DB
try:
  dbconn=psycopg2.connect(user="django",host="127.0.0.1",port="9432",database="mdm") 
except Exception as e:
  print("failed to connect to DB - is postgres running ? %s " % e )
  sys.exit(0)

#generic db query
def db_query(query):
  try:
    cur=dbconn.cursor()
    cur.execute(query)
    return(cur.fetchall())
  except:
    print("error running query %s" % query)
    sys.exit(0)

def remove_control_characters(s):  #https://stackoverflow.com/questions/4324790/removing-control-characters-from-a-string-in-python
    return "".join(ch for ch in s if unicodedata.category(ch)[0]!="C")

def get_db_info():
#fetch data for admin.user_status  
    users = db_query("select unique_machine_id,comment,timestamp with time zone 'epoch' + last_connected  * INTERVAL '1 second' from admin.user where unique_machine_id != '' order by unique_machine_id;")
    return(users)

def update_fw_customfield(clientid,state,lastconnect):  # inject values into filewave custom field defined via custom_field_name
    try:
        if state == None: return() # skip empty lines
        sanitised_state = json.dumps(remove_control_characters(state))  #remove all control characters, and make sure quotes are escaped properly.
        req_updatetime = str(datetime.datetime.now(datetime.timezone.utc).replace(microsecond=0).isoformat()+"Z").replace('+00:00','')  #example 2021-06-16T15:24:19Z
	#req_data='{"CustomFields":{"'+custom_field_name+'":{"exitCode":null,"status":0,"updateTime":"'+req_updatetime+'","value":'+sanitised_state+' }}}'
        req_data='{"CustomFields":{"'+custom_field_name+'":{"exitCode":null,"status":0,"updateTime":"'+req_updatetime+'","value":'+sanitised_state+' },  \
                  "fw_lastconnect":{"exitCode":null,"status":0,"updateTime":"'+req_updatetime+'","value":"'+lastconnect+'"} } }'

        req_uri = "inv/api/v1/client/"+clientid
        req_headers = {'Authorization':fw_token , 'Content-Type':'application/json' }
        customfield_r = requests.patch(fw_base_url+req_uri,headers=req_headers,json=json.loads(req_data))
        vprint("%s : %s" % (clientid,req_data))
        vprint("response for %s : %s " % (clientid,customfield_r.status_code))
    except Exception as e:
        print("issue setting custom field values in filewave for %s , value %s: %s" % ( clientid, sanitised_state, e) )
        try:
            print(req_data)
        except:
            pass

users=get_db_info()
for record in users:
    if record[0] != '':
         sanedate = str(record[2]).replace(' ','T').replace('+00:00','Z')
         update_fw_customfield(record[0],record[1],sanedate)
         time.sleep(0.2)

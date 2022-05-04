#!/usr/local/filewave/python/bin/python3
#updates custom field with comment, works only on FileWave server locally , and only for desktop clients. 

VERBOSE = False

# unicode characters to be used for classification , and lower bound and upper bound of delays in minutes
# more colors here : https://www.compart.com/en/unicode/search?q=large+green+circle
green=chr(128994)
yellow=chr(128993)
orange=chr(128992)
red=chr(128308)
black=chr(11044)


# defined as an array of tuples, ordered from "connected right now" to "hasn't been here in ages"
# ( color , Lower Bound ( minimum minutes ago ) , Upper Bound ( maximum minutes ago ) 
# i.e. :  yellow,3,30 means - yellow dot for a client that has reported in a minimum of 3 mins ago, and a maximum of 30 
intervals=((green,0,3),(yellow,3,30),(orange,30,60),(red,60,180),(black,-1,-1))


import requests
import sys
import datetime
import json
import psycopg2
import unicodedata
import os
import time


secrets_file=os.path.join(os.path.dirname(os.path.realpath(sys.argv[0])),'secrets.json')

# config parsing

try:
  with open(secrets_file) as f:
    d=json.load(f)
    servername=d['server_name']
    fw_token=d['server_token']
    custom_field_name=d['custom_field']
except Exception as e:
  print("Issue %s when trying to access configuration file ; please fix and retry" % e)
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
    values=cur.fetchall()
    dbconn.close() # ditch the db connection as quickly as possible
    return(values)
  except:
    print("error running query %s" % query)
    sys.exit(0)

def remove_control_characters(s):  #https://stackoverflow.com/questions/4324790/removing-control-characters-from-a-string-in-python
    return "".join(ch for ch in s if unicodedata.category(ch)[0]!="C")

def get_db_info():
#fetch data for admin.user_status  
    users = db_query("select unique_machine_id,comment,timestamp with time zone 'epoch' + last_connected  * INTERVAL '1 second',ucg_id from admin.user where unique_machine_id != '' and ucg_id is not NULL order by unique_machine_id;")
    return(users)

def mass_update_fw_customfield(client_ids,state):  # mass update the custom field for all clients having the same state , in one shot.
    try:
        req_updatetime = datetime.datetime.now().replace(microsecond=0).isoformat()+"Z"  #example 2021-06-16T15:24:19Z
        req_data='{"custom_fields":[{"name":"status_light","value":"'+state+'"}],"ucg_ids":%s}' % ( client_ids )
        vprint(req_data)
        req_uri = "inv/api/v1/custom_field/edit/"
        req_headers = {'Authorization':fw_token , 'Content-Type':'application/json' }
        customfield_r = requests.post(fw_base_url+req_uri,headers=req_headers,json=json.loads(req_data) )
        vprint("response for %s : %s " % (client_ids,customfield_r.status_code))
        if customfield_r.status_code == 503:
            time.sleep(1)
            print("retrying")
            mass_update_fw_customfield(clientid,state)
    except Exception as e:
        print("issue mass setting custom field values in filewave %s" % e)

def classify_status(timedelta, intervals): # check a timedelta and fit it into the categories defined in "intervals"
    diffminutes=timedelta // 60
    for thing in intervals:
        lowerbound=thing[1]
        upperbound=thing[2]
        if lowerbound <= diffminutes < upperbound:
            return(thing[0])
    return(intervals[-1:][0][0]) #in case we don't find any match, fall back on the last one in the chain

# prepare classes dictionary
classes={}
for category in intervals:
    classes[category[0]]=[]
vprint(classes)

users=get_db_info() 
for record in users:
    if record[0] != '':
         sanedate = str(record[2]).replace(' ','T').replace('+00:00','Z')
         last_connect_diff=datetime.datetime.now().astimezone() - record[2]
         last_connect_seconds=last_connect_diff.days * 86400 + last_connect_diff.seconds
         status_light=classify_status(last_connect_seconds, intervals)
         vprint("%s for %s seconds" % (status_light,last_connect_seconds))
         #update_fw_customfield(record[0],record[1],sanedate,status_light)
         classes[status_light].append(record[3])
         #time.sleep(0.1)

for category in classes:
    vprint("%s" % category)
    vprint("%s" % classes[category])
    mass_update_fw_customfield(classes[category],category)
    time.sleep(0.1)


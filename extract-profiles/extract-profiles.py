#!/usr/local/filewave/python/bin/python

#script to extract all profile files from a data folder to a separate folder structure
#for creating fileset-data-less clones of existing filewave servers
#(cannot model update if profile files on disk are empty)

datafolder='/usr/local/filewave/fwxserver/Data Folder'
outputfolder='./extracted-profiles'
debug=False

import psycopg2
import sys
import os
import datetime
from shutil import copyfile

def vprint(schtring):
  if debug: print(schtring)

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

#fetch data for all profile files 
file_ids = db_query("select id from admin.file where fileset_revision_id in ( select id from admin.fileset where sub_type = 22 );")

dbconn.close()

vprint(file_ids)

#assemble the paths on disk
sourcelist = []
pathlist = set()
for profile in file_ids:
  idstr=str(profile[0])
  foldername=idstr[:-2] + "00.FWD"
  pathlist.add(foldername)
  filename="FW" + idstr + "D"
  sourcelist.append(os.path.join(datafolder,foldername,filename))
  vprint("profile located at : %s" % sourcelist[-1])

#make sure destination folder, and structure inside exists
vprint('creating subpaths %s' % pathlist)
if os.path.exists(outputfolder) == False: os.mkdir(outputfolder)
for folder in pathlist:
  destinationpath = os.path.join(outputfolder,folder)
  if os.path.exists(destinationpath) == False : os.mkdir(destinationpath)

#copy files to new structure
for file in sourcelist:
  copyfile(file,file.replace(datafolder,outputfolder))

#we're done here
print("copied %s profile files to %s ; please move that folder's contents to '/usr/local/filewave/fwxserver/Data Folder' on the destination server" % (len(sourcelist),outputfolder))

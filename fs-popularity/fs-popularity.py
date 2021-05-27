#!/usr/local/filewave/python/bin/python
# fileset popularity contest - to be run on a filewave 14+ server, as a user that has permissions to write to output_path
# outputs a csv, and a html/javascript page with a sortable table and a download link to the csv
# cglattfelder - may 2021

debug = False
output_csv = "popularity.txt"
output_html = "popularity.html"
output_path = "/usr/local/filewave/fwone/"  # defaults to web admin root

# no changes should be necessary after this line

# TODO - find and display information on filesets associated via their group memberships
# TODO - inject links to payloads/$id/devices for number of clients ; payloads/$id/info for fileset ids
# TODO - performance 

import psycopg2
import sys
import operator
import os
import datetime

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

#fetch data for admin.user_status  
user_status = db_query("select user_id,fileset_revision_id,last_status,install_type from admin.user_status;")

#fetch data for filesets
filesets = db_query("select id,name from admin.fileset;")

#fetch data for associations
associations = db_query("select fileset_or_group_id,user_group_id,is_kiosk,is_software_update from admin.association;")

#fetch this server's name
server_name = db_query("select value from ios_preferences where key = 'mdm_server_host';")[0][0].replace('"','')

#we don't need more time from the DB ; disconnect here.
dbconn.close()

print("fetched %s filesets and %s status messages. processing.." % (len(filesets),len(user_status)))

# put filesets and fileset status in relation, count clients that have reported something on the fileset. 
popularity={}
for fs in filesets:
  fsid=fs[0]
  fsname=fs[1]
  popularity[fsname] = []
  popularity[fsname].append(0)
  popularity[fsname].append(fsid)
  popularity[fsname].append(0) # installed via kiosk
  popularity[fsname].append(0) # available in kiosk
  popularity[fsname].append(0) # number of associations
 
  vprint("processing fs id %s name %s" % (fsid,fsname))
  for status in user_status:
    if status[1] == fsid : 
      popularity[fsname][0] += 1         # total number of installs
      if status[3] == 1:                 # kiosk type
        if status[2] == 4 :              # installed via kiosk
          popularity[fsname][2] += 1
      if status[2] == 25 :               # available in kiosk
        popularity[fsname][3] += 1
  for assoc in associations:             # add the number of associations pointing directly to the fileset
    if fsid in assoc:  
      popularity[fsname][4] += 1
      vprint('association match found %s to %s , total count %s' % ( assoc, fsid , popularity[fsname][4] ))
  vprint("fs %s has popularity %s" % ( fsname, popularity[fsname] ))

ranked = sorted(popularity.items(), key=operator.itemgetter(1),reverse=True) # final, sorted list
vprint(ranked)

## CSV export
try:
  f = open(os.path.join(output_path,output_csv),'w')
  f.write("fileset name;reported by clients; fileset id; installed via kiosk ; available via kiosk ; number of associations\n")
  vprint("fileset name;reported by clients; fileset id;installed via kiosk ; available via kiosk; number of associations")
  for entry in ranked:
    try:
      vprint("%s;%s;%s;%s;%s;%s\n" % (entry[0],entry[1][0],entry[1][1],entry[1][2],entry[1][3],entry[1][4]))
      f.write("%s;%s;%s;%s;%s;%s\n" % (entry[0],entry[1][0],entry[1][1],entry[1][2],entry[1][3],entry[1][4]))
    except:
      print("error with %s" % entry[0])
  f.close()
except:
  print("error opening %s for writing, check your access for %s " % ( output_csv, output_path ) )
  sys.exit(0)

##HTML export

#HTML headers
f = open(os.path.join(output_path,output_html),'w')
f.write("""<HTML><HEAD><TITLE>FileSet Popularity contest</TITLE>
<STYLE>
#table tr:nth-child(even){background-color: #f2f2f2;}
body{
  font-family: Arial, Helvetica, sans-serif;
  border-collapse: collapse;
  width: 100%;
}
#table td  {
  border: 1px solid #ddd;
  padding: 6px;
}
</STYLE>""")
f.write("<h3>FileSet PopulaRity Contest ( last updated at %s )</h3>" % datetime.datetime.now())
f.write('<a href="./popularity.txt">CSV Download</a> - clicking on Column Headers sorts data, clicking on Links goes to Web Admin</a><br><br>')

#Table rows With Data,as a javascript array this time
f.write("<script>let tabledata = [\n")
for entry in ranked[:-1]:  # we have to provide a different format for the very last item in this list ..
  try:
    f.write("['%s',%s,%s,%s,%s,%s ],\n" % (entry[0].replace("\'","\\'"),entry[1][0],entry[1][1],entry[1][2],entry[1][3],entry[1][4]))
  except:
    print("error with %s" % entry[0])
entry=ranked[-1]
f.write("['%s',%s,%s,%s,%s,%s ]\n" % (entry[0].replace("'","\'"),entry[1][0],entry[1][1],entry[1][2],entry[1][3],entry[1][4]))

# finish the javascript array out nicely
f.write('];\n</script>')

# inject the javascript for sorting things when clicking on column headers
f.write('''<script>

// triggered by clicking on column headers;  switches between ascending and descending
var sortinfo = 'asc';
function sortData(column) {
if (sortinfo === "asc") {
  if (typeof(tabledata[0][column]) === "string") {   // if it's a string, we have to sort differently.
    var sortedata=tabledata.sort(function (a,b){ 
      var first=a[column].toLowerCase();
      var second=b[column].toLowerCase();
      if ( first > second ) 
        return 1;
      if ( first < second )
        return -1;
      return 0;
      });
  } else {                                          // if it's a number , things are simple. 
  var sortedata=tabledata.sort(function (a,b) { return a[column] - b[column]; } ).reverse();
  }
  sortinfo ='desc';
} else {
  if (typeof(tabledata[0][column]) === "string") {
    var sortedata=tabledata.sort(function (a,b){
      var first=a[column].toLowerCase();
      var second=b[column].toLowerCase();
      if ( first > second )
        return -1;
      if ( first < second )
        return 1;
      return 0;
      });
  } else { 
    var sortedata=tabledata.sort(function (a,b) { return a[column] - b[column]; } );
  }
  sortinfo = 'asc';
}
drawTable(sortedata)
}

// re-sorts data , destroys and redraws table

function drawTable(data) {
if (document.contains(document.getElementById('table'))){
document.getElementById('table').remove();
}
let table = document.createElement('table');
table.style.border = '1px solid black';
table.id = 'table';

//create the header row , clickable items - https://stackoverflow.com/questions/19586137/addeventlistener-using-for-loop-and-passing-values helped a lot here. 
table.insertRow();
let headerrow = ['FileSet Name','Clients','FileSet ID','Installed via Kiosk','Available via Kiosk','Number of associations'];
let cellcount = 0;
for (let cell of headerrow) {
  (function () {
  var colnr = cellcount;
  let newCell = table.rows[table.rows.length - 1].insertCell();
  newCell.textContent = cell;
  newCell.style.fontWeight = 'bold';
  newCell.addEventListener('click',function () { sortData(colnr) } );
  }());
  cellcount++;
  }
//display the popularity contest results 
for (let row of data) {
  table.insertRow();
  cellctr=0;
  fsid=row[2];
  for (let cell of row) {
    let newCell = table.rows[table.rows.length - 1].insertCell();
    newCell.textContent = cell;
    if ( cellctr === 1 ) { newCell.innerHTML = "<a href=\'/payloads/" + fsid + "/devices/\'>" + cell + "</a>" }
    if ( cellctr === 2 ) { newCell.innerHTML = "<a href=\'/payloads/" + fsid + "/info/\'>" + cell + "</a>" }
    cellctr++;
  }
}
document.body.appendChild(table);
}
sortData(1)  //by default we want the most popular ones on top. 
</script>
''')
f.write('</BODY></HTML>')

print("check out https://%s/%s for the result - provided you have left default options" % ( server_name , output_html ))
f.close()

# google_sheets-reports

Script to extract data from FileWave , and publish it in a google sheets document. 

Installation Instructions

First we have to get some python modules
```
/usr/local/filewave/python/bin/python -mvenv ./venv
. ./venv/bin/activate
pip3 install requests
pip3 install gspread
deactivate
```
Now we have to populate the json files with secrets:

token.json comes out of the google admin console ( visit [https://docs.gspread.org/en/v4.0.1/oauth2.html#enable-api-access-for-a-project](https://docs.gspread.org/en/v4.0.1/oauth2.html#enable-api-access-for-a-project) ) 
and
secrets.json comes out of the "manage administrators" assistant in FileWave Admin

Cronjob 
adapt following shell script , and schedule it to run once an hour. 

```
#!/bin/bash

cd /usr/local/complete-report
. ./venv/bin/activate
python ./complete-report.py
```

Detailed configuration inline - this script can read things you see in web admin, inventory , and custom inventory fields. 



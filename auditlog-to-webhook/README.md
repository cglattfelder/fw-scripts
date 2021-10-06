Sending the audit.log to a webhook-enabled chat service

To get audit log events posted into a chat room , like slack or google chat, schedule this script on your server to run once a minute. 

Minimal Configuration:

webhook_url = 'https://chat.googleapis.com/v1/'  #here's yours ..

message_template = {'text':''}

auditlog='/usr/local/filewave/log/audit.log'
lastlinefile='/root/auditlog-to-webhook/lastline-processed.txt'
pidfile='/root/auditlog-to-webhook/script.pid'

pause_between_lines=1 # in seconds

debug=True
send=True

sizetoread=50000   # read the last x characters in the file at every run


You have the option to prevent the script from posting lines that contain certain substrings by adding them to this dictionary :

bannedlines = ['\'type\': \'ActiveDirectory\'}]\' - SUCCESS',
  'Schedule LDAP custom field extraction - SUCCESS',
  'logged on - SUCCESS','User logged out - SUCCESS',
  'VPP incremental sync - ','is already logged on - ERROR: HTTP 409',
  'Fetching Personal Recovery Key information - ERROR: No FileVault2Device matches the given query',
  'admin name: \'fwadmin\' Save Edited Custom Fields Values - SUCCESS'
]  #any line containing the strings above will not be posted. 


.. and you can have the script remove parts of messages by adding it to the following list. 

remove_these_parts = ['adminKeyValue:.+,']  #replace empty spaces/values with .+ ; i.e. to replace Argh(anything): use Argh.+:

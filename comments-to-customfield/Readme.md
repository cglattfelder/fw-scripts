# comments_to_customfield

If you need your ( Desktop ) FileWave client comments in inventory. 

## Installation 

  Create a custom field called fw_comment , or import the custom field from fw_comment.customfields in this directory. 
  Copy the python script to your filewave server. 


## Usage

    fw_server=YOUR_SERVER_FQDN_HERE fw_inv_token="YOUR_BASE64_TOKEN_HERE" fw_customfield="fw_comment" /usr/local/filewave/python/bin/python /root/comment_to_customfield/comment_to_customfield.py


## Useful Parameters ( edit the script to modify those )

    VERBOSE = True ( False is default - script only reports errors when configured to False )

## Cronjob Example - run it every 15 minutes ( via crontab -e as root )

    */15 * * * * fw_server=YOUR_SERVER_FQDN_HERE fw_inv_token="YOUR_BASE64_TOKEN_HERE" fw_customfield="fw_comment" /usr/local/filewave/python/bin/python /root/comment_to_customfield/comment_to_customfield.py>>/tmp/comment_to_customfield.log
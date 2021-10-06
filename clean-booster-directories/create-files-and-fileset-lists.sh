#!/bin/sh

# list of files that are not used anywhere 
/usr/local/filewave/postgresql/bin/psql mdm django -t -c "select id from admin.file where fileset_revision_id in ( select id from admin.fileset where id not in ( select distinct(fileset_revision_id) from admin.user_status where fileset_revision_id is not NULL ) ) ;" >/usr/local/filewave/fwone/files-to-remove.txt

# list of fileset container ids that are not used anywhere
/usr/local/filewave/postgresql/bin/psql mdm django -t -c "select id from admin.fileset where id not in ( select distinct(fileset_revision_id) from admin.user_status where fileset_revision_id is not NULL ) ;" >/usr/local/filewave/fwone/filesets-to-remove.txt


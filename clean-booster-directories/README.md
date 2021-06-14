# clean-booster-directories

A script to clean boosters of filesets that are still contained in the Server , but are no longer requested by clients
that are being served by a the booster you run this on ; and to make sure that that booster does not re-sync those filesets 
unless clients start requesting them again. 

The script requires two files to be in the same directory as itself , here's how to create those on your filewave server beforehand : 

    /usr/local/filewave/postgresql/bin/psql mdm django -t -c "select id from admin.file where fileset_revision_id in ( select id from admin.fileset where id not in ( select distinct(fileset_revision_id) from admin.user_status where fileset_revision_id is not NULL ) ) ;" >./files-to-remove.txt

    /usr/local/filewave/postgresql/bin/psql mdm django -t -c "select id from admin.fileset where id not in ( select distinct(fileset_revision_id) from admin.user_status where fileset_revision_id is not NULL ) ;" >./filesets-to-remove.txt


Once you have copied those two files plus the script to a booster, just run (as a user that can write to /private/var/FileWave Booster/) as follows :

    bash ./clean-booster-directories.sh


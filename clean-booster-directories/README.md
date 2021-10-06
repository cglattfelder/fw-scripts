# clean-booster-directories

A script to clean boosters of filesets that are still contained in the Server , but are no longer requested by clients
that are being served by a the booster you run this on ; and to make sure that that booster does not re-sync those filesets 
unless clients start requesting them again. 

Run create-files-and-fileset-lists.sh on your filewave server peridically to create the lists of currently associated filesets.

On your boosters, run clean-booster-directories.sh , which will download the newest lists from the server. 

#!/bin/bash
# script to clean booster directories of files and fileset containers that have no associations
# to create files-to-remove.txt , run this on filewave server: 
# /usr/local/filewave/postgresql/bin/psql mdm django -t -c "select id from admin.file where fileset_revision_id in ( select id from admin.fileset where id not in ( select distinct(fileset_revision_id) from admin.user_status where fileset_revision_id is not NULL ) ) ;" >./files-to-remove.txt

# to create filesets-to-remove.txt , run this on the filewave server : 
# /usr/local/filewave/postgresql/bin/psql mdm django -t -c "select id from admin.fileset where id not in ( select distinct(fileset_revision_id) from admin.user_status where fileset_revision_id is not NULL ) ;" >./filesets-to-remove.txt

filesdeleted=0
containersdeleted=0
counter=0

owndir=$(pwd)

freespacebefore=$(df -h /private/var/FWBooster/Data\ Folder/|grep FWBooster)
filestoremovecount=$(cat ./files-to-remove.txt|wc -l)

for file in $(cat ./files-to-remove.txt) ; do 
  if [ $file -lt 1 ] ; then continue ; fi  #skip strange entries in list 
  directory=$(echo $file| sed -e 's/[0-9][0-9]$/00.FWD/')
  if [ -d /private/var/FWBooster/Data\ Folder/$directory ] ; then 
    cd /private/var/FWBooster/Data\ Folder/$directory
    for instance in $(ls FW$file* 2>/dev/null) ; do 
      rm -f ./$instance
      ((filesdeleted++))
    done
  fi
  if  (( $counter % 1000 == 0 )) ; then 
    echo "processed: $counter out of $filestoremovecount candidates ; deleted so far : $filesdeleted"
  fi
  ((counter++))
done

cd "$owndir"
for file in $(cat ./filesets-to-remove.txt) ; do
if [ $file -lt 1 ] ; then continue ; fi  #skip strange entries in list
cd /private/var/FWBooster/Data\ Folder/FILESETS
for container in $(ls FW$file* 2>/dev/null) ; do
  rm -f $container
  ((containersdeleted++))
done
done

freespaceafter=$(df -h /private/var/FWBooster/Data\ Folder/|grep FWBooster)
echo "free space before cleaning:"
echo $freespacebefore
echo "free space after cleaning:"
echo $freespaceafter

echo removed containers / filesets and versions : $containersdeleted
echo removed fileset files : $filesdeleted


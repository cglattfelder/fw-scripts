# extract-profiles

If you need to create a replica of a production FileWave Server without copying all the data , 
you won't be able to update the model on the replicaa unless you have all the configuration profile data content on disk. 
This script prepares that data in a directly copyable format , so you can get testing more quickly on your replica. 

Usage

    /usr/local/filewave/python/bin/python ./extract-profiles.py

    scp -r ./extracted-profiles/* root@destination-server:"/usr/local/filewave/Data\\ Folder/"

Useful Parameters ( edit the script to modify those )

    outputfolder='./extracted-profiles'

# ableton-tag-importer

This is a work in progress. 

Here's how it works: 
1. Use ADSR Sample Manager to auto-tag your sample-libraries
2. Launch importer.py and select the location of your ADSR Sample Manager Sqlite database
3. Select a directory from your sample library 
4. Fill in the red fields in the tag translation table to map Sample Manager tags to Ableton Tags (use the | symbol for nested tags). 
5. Press 'sync'. It will now apply the translated tags to your Ableton Live 12 library. 
6. Repeat steps 4 and 5 if necessary. 

Note that it's not required to fill the entire translation table. Tags without a translation will simply not be imported. 

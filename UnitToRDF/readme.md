UnitToRDF.py converts various units into their respective rdf graphs.

Units.json contains all the units which are needed to be converted.

For running the script
1. You need two files in your directory UnitToRDF.py  and Units.json.
2. You need to set up your local machine for Unit Transformation as described here https://docs.google.com/document/d/1I3CjYB-GDdFTZO-dHsHB0B5f0iEbzHnr8QHSKN5k3Sc/edit#

#Running the script: 

Assuming you have a "Units.json" such as the one in the "example" folder, you can run the script by doing:

 python UnitToRDF.py 
 

Executing the script will generate 3 files which are in the directory
1. dict.json which contains all the units and their respective generated URls which got successful response.
2. error.json will put those units which do not have response or are not defined yet.
3. units.ttl contains RDF graphs for all the units transformed.

#Software dependencies

To add.

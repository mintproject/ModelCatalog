#Bringing the semantics from GSN to the model catalog

This component aims to bring the semantics of the variables in the scientific variables ontology into MINT.

Requirements: pip install SPARQLWrapper

# How to run gsnvariableimport.py
There are 2 modes 
{interactive (i) and automatic(a)} 
to run this file giving command line arguments.

# Modes
Two modes are needed because there are some variables which have more than one meaning in their associated wiki pages and machine cannot detect which one is needed by user.

1. In interactive mode, run the program as python gsnvariableimport.py i . This will prompt the user each time for selecting the correct option for the corresponding variable
2. In automatic mode, run the program as python gsnvariableimport.py a . This won't prompt the user and won't add those variables which have more than 1 meaning in turtle file. It will only add those variables automatically which have only one meaning associated.

# Structure
Structure of the script is same. Running gsnvariableimport.py in any mode will generate 2 files (variable.ttl and error.json)
which is self explanatory as one(variable.ttl) will contain rdf data of all standard variables whose data is present and the other(error.json) will give the list of variables whose information is not present. 

# Model catalog: Population and linking

This repository contains the resources necessary to populate and curate the model catalog. The repository is organized as follows (see respective readme files in subfolders to know more about each of their contents):
 * AutomaticLayoutDetection: Script that given a layout file extracted automatically from a dataset, it transforms it into the DataCubes representation from W3C. 
 * CSVToRDF: Scripts to transform all model contents in /Data to RDF.
 * Data: All CSV files containing information of the models, their metadata and variables. The data is organized so the columns represent properties and data properties of the ontology, while the rows are instances described and linked in the models (e.g., input types, variables, etc.)
 * ExportCatalog: Scripts to extract the contents of the model catalogs as a series of CSVs.
 * GSNVariableImport: Scripts that query the current contents of the model catalog to extract GSNs (now SVOs) and bring the appropriate context into the model catalog. Additional links to Wikidata are created in the process. 
 * OtherTransformations: Legacy scripts to organize information about units.
 * UnitToRDF: Scripts designed to align unit labels provided by modelers (e.g., "m/day") to a semantic representation. 

## Process to export the model catalog. 
Just execute `exportModelCatalog.py`. There is a config.yaml script to indicate the graphs desired to export (each user has a graph, right now it is configured to extract the mint and texas graphs). As a result, the script will write a series of CSVs, where the first column represents an instance, the header of each column represents the property and the cell rows represent the different values. 

## Process to populate the model catalog.

1) Execute CSVToRDF. Compile and run the Java project, which will create an initial version of the turtle file with all contents from the Data folder integrated and linked. You should point the folder produced by the export Python script.

2) Extract units from labels and connect to WikiData: 
    
    You need to have access to the CCUT repository with the docker file: https://github.com/usc-isi-i2/mint-data-catalog/tree/ccut-dev
    
    1. clone the mint-data-catalog github repository 
    2. (move to ccut_docker branch)
    3. cd to ccut_docker
    4. build image
        docker build -t ccut_docker .
    5. run image (a flask server)
        docker run -d -p 5000:5000 ccut_docker run -h 0.0.0.0 -p 5000
    6. cd UnitToRDF (folder in this repository)
    7. run the following query:
    PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
    PREFIX mc: <https://w3id.org/mint/modelCatalog#>
    PREFIX dc: <http://purl.org/dc/terms/>

    SELECT distinct ?units where {
        ?a mc:usesUnit ?u.
        ?u rdfs:label ?units
    }
    On https://endpoint.mint.isi.edu/ (selecting the model catalog) and download the results as JSON in the /run folder replacing "Units.ttl"
    7. Run python UnitToRDF. This is an interactive process where the program will ask the user in case of ambiguous terms. It works by matching the wikidata symbol with the symbol of the unit (exact match)
    
3) Generate Scientific Variable Links.
    1. cd GSNVariableImport 
    2. python gsnvariableimport.py i
        The "i" option makes the process interactive. If "a" is entered instead, the system will always pick the first definition found.

 


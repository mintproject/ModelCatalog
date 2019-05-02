#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Jan 18 14:10:44 2019

@author: deborahkhider

Generates Names for cycles variables to populate the data catalog
directly
"""
 
import pandas as pd
import numpy as np

# Open the excel input file
xl = pd.ExcelFile('/Users/deborahkhider/Documents/GitHub/Mint-ModelCatalog-Ontology/modelCatalog/instances/Variables/CYCLES_input.xlsx')
#Get the name of the only sheet
name = xl.sheet_names[0]
# Parse the data on that sheet
data = xl.parse(name)
# Get the unique file name
files = np.array(data.File.unique())
# Set a directory in which to print the files
path = '/Users/deborahkhider/Documents/MINT/ModelCatalog/NameGenerated'
# Set the prefix for the names:
prefix = "CYCLES_"

for file in files:
    # Get the Short Name of the variable in the specific file
    v = data.loc[data['File'] == file]['Short Name']
    # Compose the names and print out in a file
    filename = path+'/'+prefix+file+'.txt'
    f = open(filename,'w')
    for i in v:
        listName=(prefix+i).replace(" ", "_")
        #Print it out
        f.write(listName+';')
    f.close()
        
        
    

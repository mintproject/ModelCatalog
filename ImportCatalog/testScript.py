import pandas as pd
import math
import os
def testFiles(file_name, file_uri,row_list):
    print ""
    print "Starting "+file_name
    importData = pd.read_csv(file_name)
    storedData=pd.read_csv(os.path.join("../Data/"+file_name))
    col1=[]
    col2=[]
    for col in storedData.columns:
        col1.append(col)
    for col in importData.columns:
        col2.append(col)

    diff= list(set(col1) - set(col2))
    if len(diff)!=0:
        print "Following colums are not present in one of the files."
        print diff
    else:
        for i in range(len(row_list)):
            importData_sort=importData.sort_values(file_uri)
            storedData_sort=storedData.sort_values(file_uri)
            row1= importData_sort.iloc[row_list[i],:]
            row2_df=storedData_sort.loc[storedData_sort[file_uri]==row1[file_uri]]
            if row2_df.size==0:
                print "Data is not present for: "+ row1[file_uri]+" in existing file"
            else:
                row2=row2_df.iloc[0,:]
                for col in storedData.columns:

                   if row1[col]==row2[col]:
                       continue
                   else:
                       if type(row1[col]) is not str:
                           if math.isnan(row1[col]) and math.isnan(row2[col]):
                              continue
                       elif ";" in row1[col]:
                           arr1=row1[col].split(";")
                           arr2=row2[col].split(";")
                           diff=list(set(arr1) - set(arr2))
                           if len(diff)!=0:
                                print "Following values are in one of the files for "+row1[file_uri]
                                print diff
                       else:
                           print "Data did not match for "+row1[file_uri] +" : "+ row1[col]+" , "+row2[col]

    print "Finished "+file_name
    print ""

if __name__== "__main__":

    testFiles("DatasetSpecification.csv",'https://w3id.org/okn/o/sd#DatasetSpecification',[1,2,3])
    testFiles("Image.csv",'https://w3id.org/okn/o/sd#Image',[5,6,7])
    testFiles("VariablePresentation.csv",'https://w3id.org/okn/o/sd#VariablePresentation',[0,1,2])
    testFiles("Grid.csv",'https://w3id.org/okn/o/sdm#Grid',[0,1,2])
    testFiles("Parameter.csv",'https://w3id.org/okn/o/sd#Parameter',[0,1,2])
    testFiles("Person.csv",'https://w3id.org/okn/o/sd#Person',[0,1,2])
    testFiles("TimeInterval.csv",'https://w3id.org/okn/o/sd#TimeInterval',[0,1,2])

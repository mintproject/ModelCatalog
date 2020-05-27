import pandas as pd
import os
def testFiles(file_name, file_uri,row_list):
    print ("")
    print ("Starting "+file_name)
    importData = pd.read_csv(file_name)
    storedData=pd.read_csv(os.path.join("../Data/"+file_name))
    existing_file=[]
    exported_file=[]
    for col in storedData.columns:
        existing_file.append(col)
    for col in importData.columns:
        exported_file.append(col)

    diff= list(set(existing_file) - set(exported_file))
    if len(diff)!=0:
        print ("Following colums are not present in one of the files.")
        print (diff)
    else:
        for i in range(len(row_list)):
            importData_sort=importData.sort_values(file_uri)
            storedData_sort=storedData.sort_values(file_uri)
            exported_row= importData_sort.iloc[row_list[i],:]
            row2_df=storedData_sort.loc[storedData_sort[file_uri]==exported_row[file_uri]]
            if row2_df.size==0:
                print ("Data is not present for: "+ str(exported_row[file_uri])+" in existing file")
            else:
                existing_row=row2_df.iloc[0,:]
                for col in storedData.columns:
                   first=str(exported_row[col])
                   second=str(existing_row[col])
                   if first==second:
                       continue
                   else:
                       # if type(exported_row[col]) is not str and isinstance(exported_row[col],float) and isinstance(existing_row[col],float):
                       #     type(exported_row[col])
                       #     if math.isnan(exported_row[col]) and math.isnan(existing_row[col]):
                       #        continue
                       if ";" in first:
                           arr1=first.split(";")
                           arr2=second.split(";")
                           diff=list(set(arr1) - set(arr2))
                           if len(diff)!=0:
                                print ("Following values are in one of the files for "+col+" in "+exported_row[file_uri])
                                print (diff)
                       else:
                           print ("Data did not match for "+col+" in "+ exported_row[file_uri] +" : "+ first+" , "+second)

    print ("Finished "+file_name)
    print ("")

if __name__== "__main__":

    testFiles("DatasetSpecification.csv",'https://w3id.org/okn/o/sd#DatasetSpecification',[1,6,10])
    testFiles("Image.csv",'https://w3id.org/okn/o/sd#Image',[5,6,7])
    testFiles("VariablePresentation.csv",'https://w3id.org/okn/o/sd#VariablePresentation',[1,6,10,12])
    testFiles("Grid.csv",'https://w3id.org/okn/o/sdm#Grid',[1,10,11])
    testFiles("Parameter.csv",'https://w3id.org/okn/o/sd#Parameter',[1,6,10,12])
    testFiles("Person.csv",'https://w3id.org/okn/o/sd#Person',[1,6,10,12])
    testFiles("TimeInterval.csv",'https://w3id.org/okn/o/sdm#TimeInterval',[0,1,2])
    testFiles("Process.csv",'https://w3id.org/okn/o/sdm#Process',[0,1,2])
    testFiles("Visualization.csv",'https://w3id.org/okn/o/sd#Visualization',[0,1,2])
    testFiles("FundingInformation.csv",'https://w3id.org/okn/o/sd#FundingInformation',[0,1,2])
    testFiles("Model.csv",'https://w3id.org/okn/o/sdm#Model',[0,1,2])
    testFiles("ModelConfiguration.csv",'https://w3id.org/okn/o/sdm#ModelConfiguration',[0,1,2])
    testFiles("Organization.csv",'https://w3id.org/okn/o/sd#Organization',[0,1,2])
    testFiles("Region.csv",'https://w3id.org/okn/o/sdm#Region',[0,1,2])
    testFiles("SampleResource.csv",'https://w3id.org/okn/o/sd#SampleResource',[0,1,2])
    testFiles("SourceCode.csv",'https://w3id.org/okn/o/sd#SourceCode',[0,1,2])


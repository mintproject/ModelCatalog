import requests
import csv
import yaml

def import_script(concept,class_list,data_url,query_url):
    #data_url="<http://ontosoft.isi.edu:3030/modelCatalog-1.1.0/data/mint@isi.edu>"
    #query_url = "http://ontosoft.isi.edu:3030/modelCatalog-1.1.0/query"

    class_query='prefix sd: <'+concept+'> ' \
                'SELECT distinct ?class  from '+data_url+' where{' \
                '?a a ?class.' \
                'filter(regex(str(?class), "^'+concept+'", "i"))' \
                '}'
    not_to_trim_list=["rdf-syntax-ns#type","sd#hasStandardVariable","sd#website","sd#hadPrimarySource","sd#value","sd#identifier","sd#license","sd#codeRepository","sd#hasComponentLocation","sd#hasImplementationScriptLocation"]
    PARAMS = {'query':class_query}
    r = requests.get(url = query_url,params = PARAMS)
    data = r.json()
    if len(class_list)==0:
        class_list=[]
        for i in range(len(data['results']['bindings'])):
            val=data['results']['bindings'][i]['class']['value']
            val=val.split('#')[-1]
            class_list.append(val)

    for i in range(len(class_list)):
        class_name=class_list[i]

        myquery1='PREFIX sdm: <'+concept+'>' \
                 'SELECT distinct ?a ?b ?c  from '+data_url+' where{ ' \
                 '?a a sdm:'+class_list[i]+'.' \
                 '?a ?b ?c' \
                 '}'

        header_arr=[]
        header_arr.append(concept+class_list[i])
        PARAMS = {'query':myquery1}
        r = requests.get(url = query_url,params = PARAMS)
        data = r.json()

        data_dict = {}
        for i in range(len(data['results']['bindings'])):
            a=data['results']['bindings'][i]['a']['value']
            a=a.split('/')[-1]
            b=data['results']['bindings'][i]['b']['value']
            c=data['results']['bindings'][i]['c']['value']
            if c not in header_arr and b not in header_arr:
                header_arr.append(b)
            if c not in header_arr and all(substring not in b for substring in not_to_trim_list):
                 c=c.split('/')[-1]

            if a not in data_dict:
                data_dict[a]=[]
            data_dict[a].append((b, c))

        rows=[]
        for key in data_dict:
            row={}
            for type,val in data_dict[key]:
                if val in header_arr:
                    row[val]=key
                    continue
                else:
                    if type not in row:
                        row[type]=val
                    else:
                        row[type]=row[type]+";"+val

            rows.append(row)
        rows = sorted(rows, key=lambda x:x[concept+class_name])
        with open(class_name + ".csv", 'w') as csvfile:
            csvwriter = csv.writer(csvfile)
            csvwriter.writerow(header_arr)
            for i in range(len(rows)):
                temp=[]
                for j in header_arr:
                    if j in rows[i]:
                       temp.append(rows[i][j].encode('ascii', 'ignore'))
                    else:
                         temp.append("")
                csvwriter.writerow(temp)

        print class_name + " is done"




if __name__== "__main__":

  with open("config.yml", 'r') as ymlfile:
     cfg = yaml.safe_load(ymlfile)
  data_url="<"+cfg['data_url']+">"
  query_url=cfg['query_url']
  import_script("https://w3id.org/okn/o/sd#",[],data_url,query_url)
  import_script("https://w3id.org/okn/o/sdm#",["CausalDiagram","TimeInterval","Model","Region","ModelConfiguration","Grid","Process"],data_url,query_url)

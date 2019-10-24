import requests
import csv

def import_script(concept,class_list):
    data_url="<http://ontosoft.isi.edu:3030/modelCatalog-1.1.0/data/mint@isi.edu>"
    URL = "http://ontosoft.isi.edu:3030/modelCatalog-1.1.0/query"

    class_query='prefix sd: <'+concept+'> ' \
                'SELECT distinct ?class  from '+data_url+' where{' \
                '?a a ?class.' \
                'filter(regex(str(?class), "^'+concept+'", "i"))' \
                '}'

    PARAMS = {'query':class_query}
    r = requests.get(url = URL,params = PARAMS)
    data = r.json()
    if len(class_list)==0:
        class_list=[]
        for i in range(len(data['results']['bindings'])):
            val=data['results']['bindings'][i]['class']['value']
            val=val.split('#')[-1]
            class_list.append(val)

    for i in range(len(class_list)):
        class_name=class_list[i]
        myquery='PREFIX sd: <'+concept+'> \n' \
                'SELECT distinct ?b  from '+data_url+' where{' \
                '?a a sd:'+class_list[i]+'.' \
                '?a ?b ?c' \
                '}'

        myquery1='PREFIX sdm: <'+concept+'>' \
                 'SELECT distinct ?a ?b ?c  from '+data_url+' where{ ' \
                 '?a a sdm:'+class_list[i]+'.' \
                 '?a ?b ?c' \
                 '}'

        PARAMS = {'query':myquery}

        r = requests.get(url = URL,params = PARAMS)
        data = r.json()
        header_arr=[]
        header_arr.append(concept+class_list[i])

        # for i in range(len(data['results']['bindings'])):
        #     header_arr.append(data['results']['bindings'][i]['b']['value'])
        #print header_arr

        PARAMS = {'query':myquery1}
        r = requests.get(url = URL,params = PARAMS)
        data = r.json()

        data_dict = {}
        for i in range(len(data['results']['bindings'])):
            a=data['results']['bindings'][i]['a']['value']
            a=a.split('/')[-1]
            b=data['results']['bindings'][i]['b']['value']
            c=data['results']['bindings'][i]['c']['value']
            if c not in header_arr and b not in header_arr:
                header_arr.append(b)
            if c in header_arr or "rdf-syntax-ns#type" in b or "sd#hasStandardVariable" in b or "sd#website" in b:
                c=c
            else:
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

  import_script("https://w3id.org/okn/o/sd#",[])
  import_script("https://w3id.org/okn/o/sdm#",class_list=["CausalDiagram","TimeInterval","Model","Region","ModelConfiguration","Grid","Process"])

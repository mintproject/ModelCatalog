import requests
import csv


data_url="<http://ontosoft.isi.edu:3030/modelCatalog-1.1.0/data/mint@isi.edu>"

class_query='prefix sd: <https://w3id.org/okn/o/sd#> ' \
            'PREFIX sdm: <https://w3id.org/okn/o/sdm#>' \
            'SELECT distinct ?class  from '+data_url+' where{' \
            '?a a ?class.' \
            'filter(regex(str(?class), "^https://w3id.org/okn/o/sd#", "i"))' \
            '}'

PARAMS = {'query':class_query}
URL = "http://ontosoft.isi.edu:3030/modelCatalog-1.1.0/query"

r = requests.get(url = URL,params = PARAMS)
data = r.json()
class_list=[]
for i in range(len(data['results']['bindings'])):
    val=data['results']['bindings'][i]['class']['value']
    val=val.split('#')[-1]
    class_list.append(val)

for i in range(len(class_list)):
    class_name=class_list[i]
    myquery='PREFIX sd: <https://w3id.org/okn/o/sd#> \n' \
            'SELECT distinct ?b  from '+data_url+' where{' \
            '?a a sd:'+class_list[i]+'.' \
            '?a ?b ?c' \
            '}'

    myquery1='PREFIX sdm: <https://w3id.org/okn/o/sd#>' \
             'SELECT distinct ?a ?b ?c  from '+data_url+' where{ ' \
             '?a a sdm:'+class_list[i]+'.' \
             '?a ?b ?c' \
             '}'

    PARAMS = {'query':myquery}
    URL = "http://ontosoft.isi.edu:3030/modelCatalog-1.1.0/query"

    r = requests.get(url = URL,params = PARAMS)
    data = r.json()
    header_arr=[]
    header_arr.append("https://w3id.org/okn/o/sd#"+class_list[i])

    for i in range(len(data['results']['bindings'])):
        header_arr.append(data['results']['bindings'][i]['b']['value'])
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
        if c not in header_arr:
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
                   temp.append(rows[i][j])
                else:
                     temp.append("")
            csvwriter.writerow(temp)

    print class_name + " is done"

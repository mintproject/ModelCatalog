import requests
import csv
import yaml
import os


def import_script(ontology_url, class_to_exclude, graph_uri, repository, instance_uri, output_path,use_label):

    # Filter only elements of that ontology (therwise many datatypes will be imported.
    class_query = 'prefix sd: <' + ontology_url + '> ' \
                  'SELECT distinct ?class  from ' + graph_uri + ' where{' \
                  '?a a ?class.' \
                  'filter(regex(str(?class), "^' + ontology_url + '", "i"))' \
                  '}'

    # print(class_query)
    # not_to_trim_list = ["rdf-syntax-ns#type", "sd#hasStandardVariable", "sd#website", "sd#hadPrimarySource",
    # "sd#value",
    #                     "sd#identifier", "sd#license", "sd#codeRepository", "sd#hasComponentLocation",
    #                     "sd#hasImplementationScriptLocation"]
    params = {'query': class_query}
    r = requests.get(url=repository, params=params)
    data = r.json()
    class_list = []
    for c in range(len(data['results']['bindings'])):
        value = data['results']['bindings'][c]['class']['value']
        value = value.split('#')[-1]
        if value not in class_to_exclude:
            class_list.append(value)
        else:
            print('Skipping: '+value)
    for c in class_list:
        myquery1 = 'PREFIX ex: <' + ontology_url + '>' \
                'SELECT distinct ?a ?b ?c ?l  from ' + graph_uri + ' where{ ' \
                '?a a ex:' + c + '.' \
                '?a ?b ?c.' \
                 'optional{ ?c <http://www.w3.org/2000/01/rdf-schema#label> ?l }' \
                '}'
        header_arr = []
        header_arr.append(ontology_url + c)
        params = {'query': myquery1}
        r = requests.get(url=repository, params=params)
        data = r.json()

        data_dict = {}
        for vc in range(len(data['results']['bindings'])):
            a = data['results']['bindings'][vc]['a']['value']
            a = a.replace(instance_uri, "")
            b = data['results']['bindings'][vc]['b']['value']
            c_value = data['results']['bindings'][vc]['c']['value']
            try:
                label = data['results']['bindings'][vc]['l']['value']
            except:
                # The resource does not have a label
                label = ""
            if c_value not in header_arr and b not in header_arr:
                header_arr.append(b)
            # replace URIs for local names. Special cases: Units, Variables and SoftwareImages (have just label)
            if b in use_label:
                print('Detected to use with label: ' + label)
                c_value = label
            else:
                c_value = c_value.replace(instance_uri, "")

            if a not in data_dict:
                data_dict[a] = []
            data_dict[a].append((b, c_value))

        rows = []
        for key in data_dict:
            row = {}
            for type, val in data_dict[key]:
                if val in header_arr:
                    row[val] = key
                    continue
                else:
                    if type not in row:
                        row[type] = val
                    else:
                        row[type] = row[type] + ";" + val

            rows.append(row)
        # print(rows)
        rows = sorted(rows, key=lambda x: x[ontology_url + c])
        with open(os.path.join(output_path, c+".csv"), 'w', newline='') as csvfile:
            csvwriter = csv.writer(csvfile, quoting=csv.QUOTE_MINIMAL, quotechar='"')
            csvwriter.writerow(header_arr)
            for r in rows:
                temp = []
                for j in header_arr:
                    if j in r:
                        temp.append(r[j]) #.encode('ascii', 'ignore')
                    else:
                        temp.append("")
                csvwriter.writerow(temp)

        print(c + " has been processed")


if __name__ == "__main__":
    with open("config.yml", 'r') as ymlfile:
        cfg = yaml.safe_load(ymlfile)
    query_url = cfg['query_url']
    excludedClassesSDM = ["Theory-GuidedModel","PointBasedGrid","SpatiallyDistributedGrid","StandardVariable","Subsidy"]
    excludedClassesSD = ["SoftwareImage"] # We will create them in the import script
    #import_script("https://w3id.org/okn/o/sd#", [], data_url, query_url)
    #import_script("https://w3id.org/okn/o/sdm#",
    #              ["CausalDiagram", "TimeInterval", "Model", "Region", "ModelConfiguration", "Grid", "Process"],
    #              data_url, query_url)
    outPath = cfg['outPath']
    pathGraph = outPath
    if not os.path.exists(outPath):
        os.mkdir(outPath)
    # We may want to export multiple graphs between versions (e.g., texas, mint)
    for graph in cfg['graph']:
        # print(graph)
        val = graph.split('/')[-1]
        pathGraph = os.path.join(pathGraph, val)
        if not os.path.exists(pathGraph):
            os.mkdir(pathGraph)
        graph_url = "<" + graph + ">"
        for onto in cfg['ontology']:
            # print(onto)
            import_script(onto['url'], onto['exclude'], graph_url, query_url, cfg['instance_uri_prefix'], pathGraph, cfg['useLabel'])

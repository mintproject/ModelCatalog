import requests
import json
import uuid
import pprint
import datetime
import rdflib
from rdflib import Graph, Literal, BNode, RDF, Namespace, URIRef
from rdflib.namespace import RDFS
import csv
import sys
import traceback
from SPARQLWrapper import SPARQLWrapper, JSON
import unicodedata

pp = pprint.PrettyPrinter(indent=2)

# This is a convenience method to handle api responses. The main portion of the notebook starts in the the next cell
def handle_api_response(response, print_response=False):
    parsed_response = response.json()

    if print_response:
        pp.pprint({"API Response": parsed_response})

    if response.status_code == 200:
        return parsed_response
    elif response.status_code == 400:
        raise Exception("Bad request ^")
    elif response.status_code == 403:
        msg = "Please make sure your request headers include X-Api-Key and that you are using correct url"
        raise Exception(msg)
    else:
        now = datetime.datetime.utcnow().replace(microsecond=0).isoformat()
        msg = ("\n\n\n"
               "        ------------------------------------- BEGIN ERROR MESSAGE -----------------------------------------\n"
               "        It seems our server encountered an error which it doesn't know how to handle yet. \n"
               "        This sometimes happens with unexpected input(s). In order to help us diagnose and resolve the issue, \n"
               "        could you please fill out the following information and email the entire message between ----- to\n"
               "        danf@usc.edu:\n"
               "        1) URL of notebook (of using the one from https://hub.mybinder.org/...): [*****PLEASE INSERT ONE HERE*****]\n"
               "        2) Snapshot/picture of the cell that resulted in this error: [*****PLEASE INSERT ONE HERE*****]\n"
               "\n"
               "        Thank you and we apologize for any inconvenience. We'll get back to you as soon as possible!\n"
               "\n"
               "        Sincerely, \n"
               "        Dan Feldman\n"
               "\n"
               "        Automatically generated summary:\n"
               "        - Time of occurrence: {now}\n"
               "        - Request method + url: {response.request.method} - {response.request.url}\n"
               "        - Request headers: {response.request.headers}\n"
               "        - Request body: {response.request.body}\n"
               "        - Response: {parsed_response}\n"
               "\n"
               "        --------------------------------------- END ERROR MESSAGE ------------------------------------------\n"
               "        \n\n\n"
               "        ")

        raise Exception(msg)


def api_request(metric):
    request_headers = {
        'Content-Type': "application/json"
    }
    # For real interactions with the data catalog, use api.mint-data-catalog.org
    url = "http://localhost:5000/get_canonical_json?u="+metric
    resp = requests.get(url, headers=request_headers)

    # resp = requests.get(url + "u="+metric,
    #                      headers=request_headers)

    # If request is successful, it will return 'result': 'success' along with a list of registered standard variables
    # and their record_ids. Those record_ids are unique identifiers (UUID) and you will need them down the road to
    # register variables
    parsed_response = handle_api_response(resp, print_response=False)
    return parsed_response





def create_metric_url(parsed_response):
    url_string = parsed_response["qudtp:abbreviation"]
    url_string1 = url_string + parsed_response["ccut:hasDimension"]
    url_string2 = url_string1.replace("-", "_")
    url_string3 = url_string2.replace(" ","_")
    return url_string3

def print_turtle(store):
    print("--- start: turtle ---")
    print(store.serialize(format="turtle"))
    print("--- end: turtle ---\n")


def get_dim_abbv_typ_from_json(parsed_response):
    #print(parsed_response)
    abbreviation = parsed_response["qudtp:abbreviation"]
    dimension = parsed_response["ccut:hasDimension"]
    return dimension, abbreviation

# Other way can be to traverse only values of dictionary object
def create_metric_hasPart_url(has_part):
    url = "u_"
    keys_list = ["ccut:prefix_conversion_multiplier", "ccut:prefix_conversion_offset", "ccut:exponent", "ccut:multiplier", "qudtp:conversion_multiplier", "qudtp:conversion_offset"]
    for i in sorted(has_part):
        # print ((i, has_part[i]))
        if i =="ccut:prefix" or (i =="qudtp:quantityKind" and has_part[i] != "UNKNOWN TYPE"):
            url += has_part[i].split("#")[1].lower()
            url += "_"
        elif i in keys_list:
            if has_part[i] is not None:
                url_string1 = str(int(has_part[i]))
                url_string2 = url_string1.replace("-", "_")
                url_string3 = url_string2.replace(" ", "_")
                url += url_string3
                url += "_"
        elif i == "qudtp:symbol" or (i== "ccut:hasDimension" and has_part[i] != "UNKNOWN DIMENSION"
                                    and has_part[i] != "DIMENSION NOT IN MAPPING"):
            url_string2 = has_part[i].replace("-", "_")
            url_string3 = url_string2.replace(" ", "_")
            url += url_string3
            url += "_"

    return url[:-1]


def json_to_rdf(parsed_response, store, MINT, qudtp, ccut):

    metric_url_suffix = create_metric_url(parsed_response)
    metric_dimension, metric_abbreviation = get_dim_abbv_typ_from_json(parsed_response)
    # store = Graph()
    # METRIC = "https://w3id.org/mint/instance/"
    # qudtp = "http://qudt.org/1.1/schema/qudt#"
    # ccut = "https://www.w3id.org/mint/ccut/"
    # # Bind a few prefix, namespace pairs for pretty output
    # store.bind("metric", METRIC)
    # store.bind("qudtp", qudtp)
    # store.bind("ccut", ccut)

    metric = URIRef(MINT+metric_url_suffix)
    qudtp = Namespace(qudtp)
    ccut = Namespace(ccut)


    store.add((metric, qudtp.abbreviation, Literal(metric_abbreviation)))
    store.add((metric, RDFS.label, Literal(metric_abbreviation)))
    if metric_dimension != "":
        store.add((metric, ccut.hasDimension, Literal(metric_dimension)))
    store.add((metric, RDF.type, qudtp.Unit))

    has_part = parsed_response["ccut:hasPart"]
    for i in range(len(has_part)):
        hasPart_url_1 = create_metric_hasPart_url(has_part[i])
        has_part_url = URIRef(MINT + hasPart_url_1)
        store.add((metric, ccut.hasPart, has_part_url))
        exponent = "1"

        if "ccut:prefix" in has_part[i]:
            store.add((has_part_url, ccut.prefix, URIRef(has_part[i]["ccut:prefix"])))

        if "ccut:prefixConversionMultiplier" in has_part[i]:
            store.add((has_part_url, ccut.prefixConversionMultiplier, Literal(str(has_part[i]["ccut:prefixConversionMultiplier"]))))

        if "ccut:prefixConversionOffset" in has_part[i]:
            store.add((has_part_url, ccut.prefixConversionOffset, Literal(str(has_part[i]["ccut:prefixConversionOffset"]))))

        if "ccut:exponent" in has_part[i]:
            exponent = str(has_part[i]["ccut:exponent"])
            store.add((has_part_url, ccut.exponent, Literal(exponent)))

        if "ccut:multiplier" in has_part[i]:
            store.add((has_part_url, ccut.multiplier, Literal(str(has_part[i]["ccut:multiplier"]))))

        if "qudtp:conversionMultiplier" in has_part[i]:
            store.add((has_part_url, qudtp.conversionMultiplier, Literal(str((has_part[i]["qudtp:conversionMultiplier"])))))

        if "qudtp:conversionOffset" in has_part[i]:
            store.add((has_part_url, qudtp.conversionOffset, Literal(str(has_part[i]["qudtp:conversionOffset"]))))

        if "ccut:hasDimension" in has_part[i]:
            if not str(has_part[i]["ccut:hasDimension"]).startswith("UNKNOWN"):
                store.add((has_part_url, ccut.hasDimension, Literal(str(has_part[i]["ccut:hasDimension"]))))

        if "qudtp:quantityKind" in has_part[i]:
            if not str(has_part[i]["qudtp:quantityKind"]).startswith("UNKNOWN"):
                #store.add((has_part_url, qudtp.quantityKind, Literal(str(has_part[i]["qudtp:quantityKind"]))))
                #Do not add unknown stuff. @Amrish, you should add this in the error too.
                #print("UNKNOWN part for: "+has_part_url)
            #else:
                store.add((has_part_url, qudtp.quantityKind, URIRef(has_part[i]["qudtp:quantityKind"])))

        if "qudtp:symbol" in has_part[i]:
            store.add((has_part_url, qudtp.symbol, Literal(str(has_part[i]["qudtp:symbol"]))))
            #assumption: all unit parts have a symbol.
            store.add((has_part_url, RDFS.label, Literal(str(has_part[i]["qudtp:symbol"]) +"^"+ exponent)))

    # print_turtle(store)
    # turtle_file = metric_url_suffix +".txt"
    # f = open(turtle_file, "w")
    # f.write(store.serialize(format="turtle"))
    # f.close()
    return metric, store


def add_wiki_pages(store, qudtp, owl):
    qudtp = Namespace(qudtp)
    owl = Namespace(owl)
    dict4 = {}
    wiki_dict = {}
    unit_symbol_wiki_dict = {}
    exponent_symbol_list = list()
    sparql = SPARQLWrapper("http://ontosoft.isi.edu:3030/ds/query")
    sparql_query = """
    PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
    select distinct ?symbol ?label
    where {
    ?part <https://www.w3id.org/mint/ccut#hasPart> ?symbol.
    ?symbol rdfs:label ?label.
    FILTER NOT EXISTS {
    ?symbol <https://www.w3id.org/mint/ccut#hasPart> ?p
    }
  }
            """
    sparql.setQuery(sparql_query)
    sparql.setReturnFormat(JSON)
    results = sparql.query().convert()
    for result in results["results"]["bindings"]:
        key = result['symbol']['value']
        value1 = result['label']['value']
        dict4.update({key:value1})
        value = value1.split("^")[0]
        exponent = int(value1.split("^")[1])
        if exponent != 1:
            exponent_symbol_list.append(key)

        wiki_dict.setdefault(value, []).append(key)

    for unit_symbol in wiki_dict.keys():


        sparql = SPARQLWrapper("https://query.wikidata.org/sparql")
        sparql_query = """
        select ?a ?c where {
  
        ?a wdt:P5061 \"""" + unit_symbol + """\"@en.
        ?a schema:description ?c.
        FILTER (lang(?c) = 'en')
        }
        """

        sparql.setQuery(sparql_query)
        sparql.setReturnFormat(JSON)
        results2 = sparql.query().convert()
        number_of_options = len(results2["results"]["bindings"])
        if number_of_options == 0:
            continue

        if number_of_options == 1:
            for res in results2["results"]["bindings"]:
                obj = res['a']['value']
                unit_symbol_wiki_dict.update({unit_symbol:obj})
                # store.add((URIRef(key), URIRef("http://www.geoscienceontology.org/svo/svu#hasAssociatedWikipediaPage"), URIRef(obj)))

        if number_of_options > 1:
            serial_number = 1
            request = ""
            for res in results2["results"]["bindings"]:
                description = unicodedata.normalize('NFKD', res['c']['value']).encode('ascii','ignore')
                # print(description)
                request += str(serial_number) + ": " + description.decode('utf-8') + "\n"
                serial_number += 1

            option = input("Please select the most appropriate option for the variable description\n"
                               "Variable :- " + unit_symbol + "\n"
                               + request
                               )
            try:
                option = int(option)
            except:
                option = input("Please input integer as option")
                option = int(option)
            while option < 1 or option > number_of_options:
                print ("Wrong Input.")
                option = input("Please input again")
                try:
                    option = int(option)
                except ValueError:
                    continue

            res = results2["results"]["bindings"][option - 1]
            obj = res['a']['value']
            unit_symbol_wiki_dict.update({unit_symbol: obj})
            # store.add((URIRef(key), URIRef("http://www.geoscienceontology.org/svo/svu#hasAssociatedWikipediaPage"), URIRef(obj)))

    for key, value in unit_symbol_wiki_dict.items():
        if key in wiki_dict.keys():
            uri_list = wiki_dict[key]
            for uri in uri_list:
                store.add((URIRef(uri), qudtp.quantityKind, URIRef(value)))

    for exponent_symbol in exponent_symbol_list:
        URI = exponent_symbol
        quantity_symbol = dict4[exponent_symbol]
        sparql = SPARQLWrapper("https://query.wikidata.org/sparql")
        sparql_query = """
        select ?a where {

        ?a skos:altLabel \"""" + quantity_symbol + """\"@en.
        }
        """

        sparql.setQuery(sparql_query)
        sparql.setReturnFormat(JSON)
        results3 = sparql.query().convert()
        for res in results3["results"]["bindings"]:
            obj = res['a']['value']
            store.add((URIRef(URI), owl.sameAs, URIRef(obj)))


def preprocess_turtle_file(store):
    MINT = "https://w3id.org/mint/instance/"
    qudtp = "http://qudt.org/1.1/schema/qudt#"# to fix when I get the right NS.
    ccut = "https://www.w3id.org/mint/ccut#"
    owl = 'http://www.w3.org/2002/07/owl#'
    # Bind a few prefix, namespace pairs for pretty output
    store.bind("mint", MINT)
    store.bind("qudtp", qudtp)
    store.bind("ccut", ccut)
    store.bind("owl", owl)

    return store, MINT, qudtp, ccut, owl

def create_success_json(success_dict):
    with open('dict.json', 'w') as fp:
        json.dump(success_dict, fp, indent = 2)


def create_error_json(error_dict):
    with open('error.json', 'w') as fp:
        json.dump(error_dict, fp, indent =2)


def create_turtle_file(store):
    f = open('units.ttl', "wb")
    f.write(store.serialize(format="turtle"))
    f.close()

if __name__ == '__main__':
    input_file = "run/Units.json"
    #Change this to be your file of choice
    # input_file = sys.argv[1]
    error_dict = dict()
    success_dict = dict()

    store = Graph()
    store, MINT, qudtp, ccut, owl = preprocess_turtle_file(store)

    with open(input_file, "r") as read_file:
        data = json.load(read_file)

        list_dict =  data["results"]["bindings"]
        unit_list = list()
        #print (list_dict)
        for unit_dict in list_dict:
            unit_list.append(unit_dict["units"]["value"])

        # print unit_list
    # metric = fp.readline()
        count =1
        for metric in unit_list:
            errorflag = 0
            try:
                parsed_response = api_request(metric)
                errorflag = 1
            except:
                error_dict[metric] = "Unit not Defined"

            if errorflag == 1:
                try:
                    URI, store = json_to_rdf(parsed_response, store, MINT, qudtp, ccut)
                    success_dict[metric] = URI
                    # print URI
                    count+=1
                except Exception as e:
                    print(e)
                    traceback.print_exc()
                    error_dict[metric] = "Input Error"

        create_success_json(success_dict)
        create_error_json(error_dict)

        add_wiki_pages(store, qudtp, owl)
        create_turtle_file(store)
    # parsed_response = api_request("C")
    # count =1
    # URI = json_to_rdf(parsed_response, count)
    # count+=1
    # print URI

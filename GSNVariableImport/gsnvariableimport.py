from rdflib import Graph, Literal, BNode, RDF, Namespace, URIRef
from rdflib.namespace import RDFS
import json
from SPARQLWrapper import SPARQLWrapper, JSON
import rdflib
import re
import sys


def create_turtle_file(store):
    f = open('variable.ttl', "w")
    f.write(store.serialize(format="turtle").decode('utf-8'))
    f.close()


def create_error_file(error_dict):
    with open('error.json', 'w') as fp:
        json.dump(error_dict, fp, indent=2)


if __name__ == '__main__':
    mode = sys.argv[1]
    #mode = "i"
    store = Graph()
    error_dict = dict()
    property_object_list = list()
    wiki_variable_list = list()
    wiki_data_dict = dict()
    ccut = "https://www.w3id.org/mint/ccut#"
    owl = 'http://www.w3.org/2002/07/owl#'
    store.bind("ccut", ccut)
    store.bind("owl", owl)
    ccut = Namespace(ccut)
    owl = Namespace(owl)
    sparql = SPARQLWrapper("http://endpoint.mint.isi.edu/ds/query")
    sparql.setQuery("""
    PREFIX mc: <https://w3id.org/mint/modelCatalog#>

    SELECT distinct ?u where {
        ?a mc:hasStandardVariable ?u.
    }
    """)

    sparql.setReturnFormat(JSON)
    results = sparql.query().convert()
    for result in results["results"]["bindings"]:
        standard_variable = result["u"]["value"]

        sparql = SPARQLWrapper("http://35.194.43.13:3030/ds/query")
        sparql.setQuery("""
    prefix skos: <http://www.w3.org/2004/02/skos/core#>
    PREFIX mc: <https://w3id.org/mint/modelCatalog#>
select ?u ?b ?c
where {
    ?u skos:prefLabel \"""" + standard_variable + """\" @en.
    ?u ?b ?c.
  }
""")
        sparql.setReturnFormat(JSON)
        results = sparql.query().convert()

        if not results["results"]["bindings"]:
            error_dict[standard_variable] = "No info available"
        else:
            for result in results["results"]["bindings"]:
                subject = str(result["u"]["value"])
                predicate = str(result["b"]["value"])
                object = str(result["c"]["value"])

                if predicate.endswith("hasProperty"):
                    property_object_list.append(object)
                # print(subject)
                # print predicate
                # print object
                # store.add((URIRef(subject), URIRef(predicate), Literal(object)))
                if not predicate.endswith("subLabel"):
                    if result["u"]["type"] == "uri":
                        if result["b"]["type"] == "uri":
                            if result["c"]["type"] == "uri":
                                store.add((URIRef(result["u"]["value"]), URIRef(result["b"]["value"]),
                                           URIRef(result["c"]["value"])))
                            else:
                                store.add((URIRef(result["u"]["value"]), URIRef(result["b"]["value"]),
                                           Literal(result["c"]["value"])))
    for property_object in property_object_list:
        sparql_query = """
        select  ?b ?c
                where
                {

                <""" +property_object+ """> ?b ?c.
                }
        """
        sparql.setQuery(sparql_query)
        sparql.setReturnFormat(JSON)
        property_results = sparql.query().convert()

        for property_result in property_results["results"]["bindings"]:
            subject = property_object
            predicate = property_result["b"]["value"]
            obj = str(property_result["c"]["value"])

            if not predicate.endswith("subLabel") and not predicate.endswith("comment"):
                if predicate.endswith("isTypeOf"):
                    property_object_list.append(obj)
                if predicate.endswith("hasUnits"):
                    obj1 = obj.replace("^", "")
                    obj = obj1
                    store.add((URIRef(subject), ccut.hasDimension, Literal(obj)))
                    continue

                if predicate.endswith("label"):
                    obj1 = obj.replace("_", " ")
                    wiki_data_dict[obj1] = subject

                # if predicate.endswith("hasAssociatedWikipediaPage"):
                #     obj1 = str(obj).split("wiki/", 1)[1]
                #     obj1 = obj1.lower()
                #     obj2 = obj1.replace("_", " ")
                #     obj2 = str(obj2).split("#",1)[0]
                #     wiki_variable_list.add(obj2)

                if property_result["b"]["type"] == "uri":
                    if property_result["c"]["type"] == "uri":
                        store.add((URIRef(subject), URIRef(predicate),
                                   URIRef(obj)))
                    else:
                        store.add((URIRef(subject), URIRef(predicate),
                                   Literal(obj)))
    # print wiki_data_dict
    wiki_variable_list = wiki_data_dict.keys()
    # print wiki_variable_list
    sparql = SPARQLWrapper("https://query.wikidata.org/sparql")
    for wiki_var in wiki_variable_list:
        sparql_query = """
        select ?a ?c where {?a rdfs:label \"""" + wiki_var +"""\"@en.
                            ?a schema:description ?c.
                           FILTER (lang(?c) = 'en')}
        """

        sparql.setQuery(sparql_query)
        sparql.setReturnFormat(JSON)
        results2 = sparql.query().convert()
        number_of_options = len(results2["results"]["bindings"])

        if number_of_options == 0:
            continue

        if number_of_options == 1:
            for res in results2["results"]["bindings"]:
                value = res['c']['value']
                subject = res['a']['value']
                store.add((URIRef(wiki_data_dict[wiki_var]), owl.sameAs, URIRef(subject)))
                store.add((URIRef(wiki_data_dict[wiki_var]), URIRef("https://schema.org/description"), Literal(value)))

        if mode == 'i':
            if number_of_options > 1:
                serial_number = 1
                request = ""
                for res in results2["results"]["bindings"]:
                    value = res['c']['value']
                    request += str(serial_number)+": " + str(value + "\n")
                    serial_number+=1

                option = input("Please select the most appropriate option for the variable description\n"
                                   "Variable :-" + wiki_var + "\n"
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
                value = res['c']['value']
                subject = res['a']['value']
                store.add((URIRef(wiki_data_dict[wiki_var]), owl.sameAs, URIRef(subject)))
                store.add((URIRef(wiki_data_dict[wiki_var]), URIRef("https://schema.org/description"), Literal(value)))


    create_turtle_file(store)
    create_error_file(error_dict)

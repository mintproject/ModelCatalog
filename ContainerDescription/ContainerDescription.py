from rdflib import Graph, Literal, BNode, RDF, Namespace, URIRef
from rdflib.namespace import RDFS
import json
from SPARQLWrapper import SPARQLWrapper, JSON
from urllib.parse import unquote


sparql = SPARQLWrapper("http://ontosoft.isi.edu:3030/ds/query")
sparql_query = """PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
select distinct ?container
where {
    ?a <http://ontosoft.org/software#hasSoftwareImage> ?container.

  }"""

def create_turtle_file(store):
    f = open('description.ttl', "wb")
    f.write(store.serialize(format="turtle"))
    f.close()

def read_file(input_file):
    with open(input_file, "r") as read_file:
        data = read_file.read()
    return data


if __name__ == '__main__':
    store = Graph()
    input_file = "thesis_2019-05-02_17-53-42.txt"
    data = read_file(input_file)
    mint = 'http://w3id.org/mint/instance'
    data = data.replace('http://dockerpedia.inf.utfsm.cl', str(mint))
    # data = data.decode('utf-8')
    data = unquote(data)
    store.parse(data=data, format="nt")
    create_turtle_file(store)

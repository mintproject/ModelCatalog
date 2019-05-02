from rdflib import Graph, Literal, BNode, RDF, Namespace, URIRef
from rdflib.namespace import RDFS
import json
import yaml

def get_layout_data_as_Json(input_file):
    with open(input_file, 'r') as fin:
        data = yaml.safe_load(fin)
        return data

def preprocess_turtle_file(ontology_prefixes, store):
    for key, val in ontology_prefixes.items():
        store.bind(key, val)
    mint = "https://mint.isi.edu/"
    qb = "http://purl.org/linked-data/cube#"
    eg = "http://example.org/ns#"
    store.bind("qb", qb)
    store.bind("eg", eg)
    eg = Namespace(eg)
    qb = Namespace(qb)
    store.add((eg.dsd_le, RDF.type, qb.DataStructureDefinition))
    return mint, qb, eg


def create_turtle_file(store):
    f = open('variable.ttl', "wb")
    f.write(store.serialize(format="turtle"))
    f.close()


def get_resource_format(data):
    return data['resources']


def get_variable_uri(variable, mint):
    underscore = variable.find("_")
    variable_uri_string = variable
    if underscore != -1:
        variable_uri_string = variable.replace("_", "")
        variable_uri_string = variable_uri_string[:underscore] + variable_uri_string[underscore:].capitalize()
    variable_uri = URIRef(mint + variable_uri_string)
    return variable_uri


def add_location_data(store, variable_uri, resource_format, location_data):
    if resource_format == 'csv':
        row_min = ""
        row_max = ""
        column_min = ""
        column_max = ""
        row_step = ""
        column_step = ""
        row = location_data.split(":")[0]
        if ';' in row:
            row = row.split(";")[0]
            row_step = row.split(";")[0]
        column = location_data.split(":")[1]
        if ';' in column:
            column = column.split(";")[0]
            column_step = column.split(";")[0]
        row_min = row
        row_max = row
        column_min = column
        column_max = column
        if ".." in row:
            row_min = row_min.rstrip("..")
            row_max = "infinity"
        if ".." in column:
            column_min = column_min.rstrip("..")
            column_max = "infinity"
        bnode = BNode()
        store.add((variable_uri, Literal("location"), bnode))
        store.add((bnode, Literal("row_min"), Literal(row_min)))
        store.add((bnode, Literal("row_max"), Literal(row_max)))
        store.add((bnode, Literal("column_min"), Literal(column_min)))
        store.add((bnode, Literal("column_max"), Literal(column_max)))
        if row_step != "":
            store.add((bnode, Literal("row_step"), Literal(row_step)))

        if column_step != "":
            store.add((bnode, Literal("column_step"), Literal(column_step)))



def add_semantic_information(store, semantic_types, variable, variable_uri, count):
    bnode = BNode()
    store.add((eg.dsd_le, qb.component, bnode))
    class_predicate = semantic_types[variable]
    variable_class, variable_predicate = class_predicate.split("--")
    prefix, clss, node = variable_class.split(":")
    node = "#" + node
    if prefix in list(ontology_prefixes.keys()):
        variable_class_uri = str(ontology_prefixes[prefix] + clss + node)
        store.add((variable_uri, RDF.type, URIRef(variable_class_uri)))
    if variable_predicate == 'rdf:value':
        store.add((bnode, qb.measure, variable_uri))
        store.add((variable_uri, RDF.type, RDF.Property))
        store.add((variable_uri, RDF.type, qb.MeasureProperty))

    else:
        store.add((bnode, qb.dimension, variable_uri))
        store.add((bnode, qb.order, Literal(count)))
        store.add((variable_uri, RDF.type, RDF.Property))
        store.add((variable_uri, RDF.type, qb.DimensionProperty))
        count+=1
    return count

def add_semantic_relations(store, semantic_relations, ontology_prefixes):
    for semantic_relation in semantic_relations:
        subject, predicate, obj = semantic_relation.split('--')
        prefix_subject, class_subject, node_subject = subject.split(":")
        node_subject = "#" + node_subject

        prefix_predicate, class_predicate = predicate.split(":")

        prefix_obj, class_obj, node_obj = obj.split(":")
        node_obj = "#" + node_obj

        subject_uri = str(ontology_prefixes[prefix_subject] + class_subject + node_subject)
        predicate_uri = str(ontology_prefixes[prefix_predicate] + class_predicate)
        obj_uri = str(ontology_prefixes[prefix_obj] + class_obj + node_obj)
        store.add((URIRef(subject_uri), URIRef(predicate_uri), URIRef(obj_uri)))

def add_dimension_mappings(store, mappings, mint):
    for mapping in mappings:
        predicate = mapping['type']
        value = mapping['value']
        value1, value2 = value.split('<->')
        variable1 = value1.split(":")[0].strip()
        variable2 = value2.split(":")[0].strip()
        variable_uri_1 = get_variable_uri(variable1, mint)
        variable_uri_2 = get_variable_uri(variable2, mint)
        store.add((variable_uri_1, Literal(predicate), Literal(value)))
        store.add((variable_uri_2, Literal(predicate), Literal(value)))


if __name__ == '__main__':
    input_file = "preprocessing_approach.model.yml"

    # Converting data to JSOM
    data = get_layout_data_as_Json(input_file)

    # getting format of the data file for which layout is given eg csv, netCDF, JSON etc
    resource_format = get_resource_format(data)
    # initializing rdf graph
    store = Graph()
    ontology_prefixes = data['semantic_model']['ontology_prefixes']
    mint, qb, eg = preprocess_turtle_file(ontology_prefixes, store)

    variable_list = list(data['layout'].keys())
    count = 1
    for variable in variable_list:
        variable_uri = get_variable_uri(variable, mint)

        count = add_semantic_information(store, data['semantic_model']['semantic_types'], variable, variable_uri, count)

        # adding location data based on resource format
        location_data = data['layout'][variable]
        add_location_data(store, variable_uri, resource_format, location_data)

    # Adding semantic relations as triples
    semantic_relations = data['semantic_model']['semantic_relations']
    add_semantic_relations(store, semantic_relations, ontology_prefixes)

    # Adding dimension mapping
    mappings = data['mappings']
    add_dimension_mappings(store, mappings, mint)

    create_turtle_file(store)

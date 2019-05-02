from SPARQLWrapper import SPARQLWrapper, JSON

#Query to retrieve labels of variables 

#sparql = SPARQLWrapper("http://ontosoft.isi.edu:3030/ds/query")
#sparql.setQuery("""
#PREFIX mc: <https://w3id.org/mint/modelCatalog#>

#SELECT distinct ?u where {
	#?a mc:hasStandardVariable ?u.
#}
#""")

#Query to retrieve variables from their label

sparql = SPARQLWrapper("http://35.194.43.13:3030/ds/query")
sparql.setQuery("""
    prefix skos: <http://www.w3.org/2004/02/skos/core#>

select ?u ?b ?c
where {
    ?u skos:prefLabel "atmosphere_water__rainfall_mass_flux"@en .
    ?u ?b ?c.
  }
""")
sparql.setReturnFormat(JSON)
results = sparql.query().convert()

for result in results["results"]["bindings"]:
    print(result["u"]["value"])
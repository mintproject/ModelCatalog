package edu.isi.csvtordf;

import com.google.gson.JsonElement;
import com.google.gson.JsonObject;
import com.google.gson.JsonParser;
import com.google.gson.stream.JsonReader;
import java.io.BufferedReader;
import java.io.FileNotFoundException;
import java.io.FileOutputStream;
import java.io.FileReader;
import java.io.IOException;
import java.io.OutputStream;
import java.net.URI;
import java.net.URLEncoder;
import java.util.Arrays;
import org.apache.jena.ontology.Individual;
import org.apache.jena.ontology.OntClass;
import org.apache.jena.ontology.OntModel;
import org.apache.jena.ontology.OntProperty;
import org.apache.jena.ontology.OntResource;
import org.apache.jena.query.Query;
import org.apache.jena.query.QueryExecution;
import org.apache.jena.query.QueryExecutionFactory;
import org.apache.jena.query.QueryFactory;
import org.apache.jena.query.ResultSet;
import org.apache.jena.rdf.model.ModelFactory;
import org.apache.jena.rdf.model.Property;

/**
 * @author dgarijo
 */
public class CSV2RDF {
    OntModel instances;
    OntModel mcOntology;
    String instance_URI = "https://w3id.org/mint/instance/";
    JsonObject unitDictionary;
    
    /**
     * @param unitDictionaryFile File containing a dictionary between unit labels and their URIs.
     * @param scientificVariableFile  File containing the RDF extraction from GSN.
     */
    public CSV2RDF(String unitDictionaryFile, String scientificVariableFile) throws FileNotFoundException{
        instances = ModelFactory.createOntologyModel();
        //we read all the variables, as they will be part of the model catalog.
        instances.read(scientificVariableFile);
        mcOntology = ModelFactory.createOntologyModel();
        mcOntology.read("https://w3id.org/mint/modelCatalog");
       // mcOntology.read("http://purl.org/dc/terms/");
//        mcOntology.read("https://knowledgecaptureanddiscovery.github.io/Mint-ModelCatalog-Ontology/modelCatalog/release/0.2.0/ontology.xml");
        mcOntology.read("http://ontosoft.org/ontology/software/ontosoft-v1.0.owl");//for some reason, it doesn't do the negotiation rihgt.
//        mcOntology.write(System.out);
        //read unit dictionary
        //
        JsonReader reader = new JsonReader(new FileReader(unitDictionaryFile));
        unitDictionary = new JsonParser().parse(reader).getAsJsonObject();
        //System.out.println(unitDictionary.get("kg/kg").getAsString());
        
        System.out.println("MINT model catalog ontology loaded. Unit dictionary loaded");
    }
    
    private void processFile(String path){
        String line = "";
        String cvsSplitBy = ",";
        String[] colHeaders = null;
        System.out.println("\nProcessing: "+path);
        try (BufferedReader br = new BufferedReader(new FileReader(path))) {
            while ((line = br.readLine()) != null) {
                String[] values = line.split(cvsSplitBy);
                if (colHeaders == null){
                    colHeaders = values;//first line
                }else{
                    //add individual (col 0)
//                    System.out.println("Values: "+Arrays.toString(values));
                    if( values!=null && values.length>0){//empty line
                        Individual ind = instances.createClass(colHeaders[0]).createIndividual(instance_URI+values[0]);
                        for(int i =1; i<values.length;i++){
                            String rowValue = values[i].trim();
                            if(!rowValue.equals("")){
                                String property = colHeaders[i];
//                                System.out.println("Processing "+ property);
//                                System.out.println(rowValue);
                                OntProperty p;
                                //this is a hack because this prop is not on the ontology
                                if(property.contains("https://w3id.org/mint/modelCatalog#hasCanonicalName")){ 
    //                                    ||
    //                                    property.contains("http://ontosoft.org/software#hasDocumentation")){
                                    p = (OntProperty) mcOntology.createDatatypeProperty(property);
                                }
                                else{
                                    p = mcOntology.getOntProperty(property);
                                }
                                if(p.isDatatypeProperty()|| p.isAnnotationProperty()||
                                        p.toString().contains("hasContainer")){
                                    //container will be separated, but for the moment it is a literal.
                                    //to include rdfs label too
                                    ind.addProperty(p, rowValue);
                                    //System.out.print(rowValue+" ");
                                }else{
                                    OntClass range = p.getRange().asClass();
                                    //this works under the assumption that there is a single range class for a property.
                                    if(rowValue.contains(";")){//multiple values
                                        String[] valuesAux = rowValue.split(";");
                                        for(String a:valuesAux){
                                            if(!a.equals("")){
                                                Individual targetIndividual = instances.getIndividual(instance_URI+a);
                                                if(targetIndividual == null){
                                                    //In unions we don't know which class is the correct one, hence "Thing"
                                                    if(range.isUnionClass()){
                                                        range = instances.getOntClass("<http://www.w3.org/2002/07/owl#Thing>");
                                                    }
                                                    targetIndividual = instances.createIndividual(instance_URI+a,range);
                                                }
                                                ind.addProperty((Property) p, targetIndividual);
                                            }
                                        }
                                    }else{
                                        //Assumming only a single type per row
                                        if(p.toString().equals("http://www.w3.org/1999/02/22-rdf-syntax-ns#type")){
                                            ind.addProperty((Property) p, instances.createIndividual(rowValue,range));
                                        }else if(p.toString().contains("usesUnit")){
                                            //mapping to the unit conversion files. A variable can only have a unit assigned
                                            JsonElement unitElement = this.unitDictionary.get(rowValue);
                                            if(unitElement!=null){
                                                //unit is found. Add its URI
                                                ind.addProperty((Property) p, instances.createIndividual(unitElement.getAsString(),instances.createClass("http://qudt.org/1.1/schema/qudt#Unit")));
                                            }else{
                                                //add empty unit with label
                                                Individual emptyUnit = instances.createIndividual(instance_URI+URLEncoder.encode(rowValue, "UTF-8"),instances.createClass("http://qudt.org/1.1/schema/qudt#Unit"));
                                                emptyUnit.addLabel(rowValue, null);
                                                ind.addProperty((Property) p, emptyUnit);
                                            }
                                        }else if(p.toString().contains("hasStandardVariable")){
                                            /**
                                            read label, try to find one in the svo file (there should be).
                                            * If found, then use that URI. IF not found, then create one.
                                            **/
                                           Query query = QueryFactory.create("select ?var where {"
                                                   + "?var <http://www.w3.org/2000/01/rdf-schema#label> \""+rowValue+"\"}");
                                           // Execute the query and obtain results
                                           QueryExecution qe = QueryExecutionFactory.create(query, instances);
                                           ResultSet rs =  qe.execSelect();
                                           if(rs.hasNext()){
                                               ind.addProperty(p, rs.next().getResource("?var"));
                                           }else{
                                               //no variable found: create variable, add label
                                               Individual userInstance = instances.createClass("http://www.geoscienceontology.org/svo/svu#Variable").
                                                       createIndividual(instance_URI+encode(rowValue));
                                               userInstance.addLabel(rowValue, null);
                                           }
                                        }
                                        else{
                                            Individual targetIndividual = instances.getIndividual(instance_URI+rowValue);
                                            if(targetIndividual == null){
                                                if(range.isUnionClass()){
                                                    range = instances.getOntClass("<http://www.w3.org/2002/07/owl#Thing>");
                                                }
                                                targetIndividual = instances.createIndividual(instance_URI+rowValue,range);
                                            }
                                            ind.addProperty((Property) p, targetIndividual);
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }

        } catch (IOException e) {
            System.err.println("Error"+e.getMessage());
        }
    }
    
    /**
     * Encoding of the name to avoid any trouble with spacial characters and spaces
     * @param name Name to encode
     * @return encoded name
     */
    public static String encode(String name){
        name = name.replace("http://","");
        String prenom = name.substring(0, name.indexOf("/")+1);
        //remove tabs and new lines
        String nom = name.replace(prenom, "");       
        nom = nom.replace("\\n", "");
        nom = nom.replace("\n", "");
        nom = nom.replace("\b", "");
        nom = nom.replace("/","_");
        nom = nom.replace("=","_");
        nom = nom.trim();
        nom = nom.toUpperCase();
        try {
            nom = new URI(null,nom,null).toASCIIString();//URLEncoder.encode(nom, "UTF-8");
        }
        catch (Exception ex) {
            System.err.println("Problem encoding the URI:" + nom + " " + ex.getMessage() );
        }
        return prenom+nom;
    }
    
    /**
     * Function to export the stored model as an RDF file, using ttl syntax
     * @param outFile name and path of the outFile must be created.
     */
    public static void exportRDFFile(String outFile, OntModel model, String mode){
        OutputStream out;
        try {
            out = new FileOutputStream(outFile);
            model.write(out,mode);
            //model.write(out,"RDF/XML");
            out.close();
        } catch (Exception ex) {
            System.out.println("Error while writing the model to file "+ex.getMessage() + " oufile "+outFile);
        }
    }
    
    public static void main(String[] args){
        try{
            //TO DO: Read path to data folder from input. Assuming the structure.
            String pathToInstancesDataFolder = "C:\\Users\\dgarijo\\Documents\\GitHub\\ModelCatalog\\Data";
            String pathToTransformationsDataFolder = "C:\\Users\\dgarijo\\Documents\\GitHub\\ModelCatalog\\Data\\Transformations";
            CSV2RDF test = new CSV2RDF(pathToInstancesDataFolder+"\\Units\\dict.json", pathToInstancesDataFolder+"\\SVO\\variable.ttl");
            
            test.processFile(pathToInstancesDataFolder+"\\Model.csv");
            test.processFile(pathToInstancesDataFolder+"\\ModelConfiguration.csv");
            test.processFile(pathToInstancesDataFolder+"\\DatasetSpecification.csv");
            test.processFile(pathToInstancesDataFolder+"\\VariablePresentation.csv");
            test.processFile(pathToInstancesDataFolder+"\\ModelVersion.csv");
            test.processFile(pathToInstancesDataFolder+"\\Process.csv");
            test.processFile(pathToInstancesDataFolder+"\\Parameter.csv");
            test.processFile(pathToInstancesDataFolder+"\\TimeInterval.csv");
            test.processFile(pathToInstancesDataFolder+"\\CAG.csv");
            test.processFile(pathToTransformationsDataFolder+"\\SoftwareScript.csv");
            test.processFile(pathToTransformationsDataFolder+"\\SoftwareVersion.csv");
            exportRDFFile("modelCatalog.ttl", test.instances, "TTL");
            exportRDFFile("modelCatalog.json", test.instances, "JSON-LD");
        }catch (Exception e){
            System.err.println("Error: "+e);
        }
    }
    
}

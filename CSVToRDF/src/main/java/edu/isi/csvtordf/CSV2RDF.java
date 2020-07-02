package edu.isi.csvtordf;

import com.google.gson.JsonElement;
import com.google.gson.JsonObject;
import com.google.gson.JsonParser;
import com.google.gson.stream.JsonReader;
import com.opencsv.CSVReader;
import java.io.BufferedReader;
import java.io.File;
import java.io.FileNotFoundException;
import java.io.FileOutputStream;
import java.io.FileReader;
import java.io.IOException;
import java.io.OutputStream;
import java.net.URI;
import java.net.URLEncoder;
import org.apache.jena.ontology.Individual;
import org.apache.jena.ontology.OntClass;
import org.apache.jena.ontology.OntModel;
import org.apache.jena.ontology.OntProperty;
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
    String instance_URI = "https://w3id.org/okn/i/mint/";
    JsonObject unitDictionary;
    
    /**
     * @param unitDictionaryFile File containing a dictionary between unit labels and their URIs.
     * @param scientificVariableFile  File containing the RDF extraction from GSN.
     */
    public CSV2RDF(String unitDictionaryFile, String scientificVariableFile) throws FileNotFoundException{
        instances = ModelFactory.createOntologyModel();
        //create class 
        instances.createClass("https://w3id.org/okn/o/sd/#SoftwareConfiguration");
        //we read all the variables, as they will be part of the model catalog.
        instances.read(scientificVariableFile);
        mcOntology = ModelFactory.createOntologyModel();
        mcOntology.read("https://w3id.org/okn/o/sdm#");
        mcOntology.read("https://w3id.org/okn/o/sd#");
        //for some reason it's not doing the right redirect
//        mcOntology.read("https://mintproject.github.io/Mint-ModelCatalog-Ontology/release/1.4.0/ontology.xml");
//        mcOntology.read("http://ontosoft.org/ontology/software/ontosoft-v1.0.owl");//for some reason, it doesn't do the negotiation rihgt.
//        mcOntology.write(System.out);
        //read unit dictionary
//        mcOntology.write(System.out);
        //
        JsonReader reader = new JsonReader(new FileReader(unitDictionaryFile));
        unitDictionary = new JsonParser().parse(reader).getAsJsonObject();
        //System.out.println(unitDictionary.get("kg/kg").getAsString());
        
        System.out.println("MINT model catalog ontology loaded. Scientific variable file loaded. Unit dictionary loaded");
    }
    
    private void checkFile (String path){
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
//                    System.out.println("Values: "+Arrays.toString(values));
                    if( values!=null && values.length>0){//empty line
                        for(int i =1; i<values.length;i++){
                            String property = colHeaders[i];
                            //System.out.println("Processing "+ property);
                            OntProperty p = mcOntology.getOntProperty(property);
                            if(p==null){
                                System.out.println("\tProblem in "+ property);
                            }else{
                                System.out.println("\tOK ");
                            }
                        }
                    }
                }
            }
        }catch(Exception e){
            System.out.println(e);
        }
                                
    }
    
    /**
     * Bit of code that queries the svo file to check if a variable (entered as plain text) corresponds to an SVO.
     * If not, creates a local URI.
     * @param ind
     * @param p
     * @param rowValue 
     */
    private void processSVO(Individual ind, Property p, String rowValue, boolean index){
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
           Individual userInstance;
           //if(index){
           // userInstance = instances.createClass("https://w3id.org/okn/o/sdm#NumericalIndex").createIndividual(instance_URI+encode(rowValue));   
           //}else{
            userInstance = instances.createClass("http://www.geoscienceontology.org/svo/svu#Variable").createIndividual(instance_URI+encode(rowValue));
           //}
           userInstance.addLabel(rowValue, null);
           //assign the variable to target node.
           ind.addProperty(p, userInstance);
       }
    }
    
    private void processFile(String path){
        String[] colHeaders = null;
        String[] values;
        System.out.println("\nProcessing: "+path);
        try{
             CSVReader reader = new CSVReader(new FileReader(path));
             while ((values = reader.readNext()) != null){
                if (colHeaders == null){
                    colHeaders = values;//first line
                }else{
//                    System.out.println("Values: "+Arrays.toString(values));
                    if( values!=null && values.length>0 && !values[0].equals("")){//empty line
                        Individual ind = instances.createClass(colHeaders[0]).createIndividual(instance_URI+values[0]);
                        for(int i =1; i<values.length;i++){
                            String rowValue = values[i].trim();
                            if(!rowValue.equals("")){
                                String property = colHeaders[i];
//                                System.out.println("Processing "+ property);
//                                System.out.println(rowValue);
                                OntProperty p;
                                //this is a hack because this prop is not on the ontology
                                if(property.contains("https://w3id.org/okn/o/sd#hasCanonicalName")){ 
                                    p = (OntProperty) mcOntology.createDatatypeProperty(property);
                                }
                                else{
                                    p = mcOntology.getOntProperty(property);
                                }
                                if(p.isDatatypeProperty()|| p.isAnnotationProperty()){
                                    //remove ""
                                    if(rowValue.startsWith("\"")){
                                        rowValue = rowValue.substring(1, rowValue.length()-1);
                                    }
                                    ind.addProperty(p, rowValue);
                                    
                                }else{
                                    OntClass range = null;
                                    if(p.getRange()!=null){
                                        range = p.getRange().asClass();
                                    }
                                    if(rowValue.contains(";")){//multiple values
                                        String[] valuesAux = rowValue.split(";");
                                        for(String a:valuesAux){
                                            if(!a.equals("")){
                                                Individual targetIndividual= instances.getIndividual(instance_URI+a);
                                                if(a.startsWith("http")){//already a URL, may happen for sd:hadPrimarySource
                                                    targetIndividual = instances.getIndividual(a);
                                                }
                                                if(targetIndividual == null){
                                                    //In unions we don't know which class is the correct one, hence "Thing"
                                                    if(range ==null||range.isUnionClass()){
                                                        range = instances.getOntClass("http://www.w3.org/2002/07/owl#Thing");
                                                    }
                                                    String aux = a;
                                                    if(!a.startsWith("http")){//already a URL, may happen for prov:hadPrimarySource
                                                        aux = instance_URI+a;
                                                    }
                                                    targetIndividual = instances.createIndividual(aux,range);
                                                }
                                                ind.addProperty((Property) p, targetIndividual);
                                            }
                                        }
                                    }else{
                                        //Assumming only a single type per row
                                        if(p.toString().equals("http://www.w3.org/1999/02/22-rdf-syntax-ns#type")){
                                            ind.addProperty((Property) p, instances.createIndividual(rowValue,range));
                                        }else if(p.toString().contains("usesUnit") ||p.toString().contains("intervalUnit")){
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
                                            processSVO(ind, p, rowValue,false);
                                        }
                                        //else if(p.toString().contains("usefulForCalculatingIndex")){
                                        //    processSVO(ind, p, rowValue,true);
                                        //}
                                        else if(p.toString().contains("hasSoftwareImage")){
                                            //seaparated because here we will do the link to Dockerpedia when appropriate.
                                            //at the moment just create a URI and link with label
                                            Individual softwareImage = instances.createIndividual(instance_URI+encode(rowValue),range);
                                            softwareImage.addLabel(rowValue, null);
                                            ind.addProperty(p, softwareImage);
                                        }
                                        else{
                                            //regular individual linking
                                            Individual targetIndividual = instances.getIndividual(instance_URI+rowValue);
                                            if(targetIndividual == null){
                                                if(range == null || range.isUnionClass()){
                                                    range = instances.getOntClass("http://www.w3.org/2002/07/owl#Thing");
                                                }
                                                String aux = rowValue;
                                                if(!rowValue.startsWith("http")){//already a URL, may happen for prov:hadPrimarySource
                                                    aux = instance_URI+rowValue;
                                                }
                                                targetIndividual = instances.createIndividual(aux,range);
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
            System.err.println("Error (likely the property has not been recognized) "+e.getMessage());
        }
    }
    
    /**
     * Encoding of the name to avoid any trouble with spacial characters and spaces
     * @param name Name to encode
     * @return encoded name
     */
    public static String encode(String name){
        name = name.replace("http://","");
        //String prenom = name.substring(0, name.indexOf("/")+1);
        //remove tabs and new lines
        String nom = name;//name.replace(prenom, "");       
        nom = nom.replace("\\n", "");
        nom = nom.replace("\n", "");
        nom = nom.replace("\b", "");
        nom = nom.replace("/","-");
        nom = nom.replace("=","-");
        nom = nom.replace(":", "%3A");
        nom = nom.replace(",", "%2C");
        nom = nom.trim();
        nom = nom.toUpperCase();
        try {
            nom = new URI(null,nom,null).toASCIIString();//URLEncoder.encode(nom, "UTF-8");
        }
        catch (Exception ex) {
            System.err.println("Problem encoding the URI:" + nom + " " + ex.getMessage() );
        }
        return nom;
        //return prenom+nom;
    }
    
    /**
     * Function to export the stored model as an RDF file, using ttl syntax
     * @param outFile name and path of the outFile must be created.
     * @param model
     * @param mode
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
    
    public static void processDataFolder(String path, boolean test, CSV2RDF instance){
        File folderInstances = new File(path);
        if(instance == null){
            System.err.println("Not initialized");
            return;
        }
        if(folderInstances.exists() && folderInstances.isDirectory()){
            for (File f: folderInstances.listFiles()){
                if (f.isDirectory()){
                    processDataFolder(f.getAbsolutePath(), test, instance);
                }else if(f.getName().endsWith("csv")){
                    processFile(f.getAbsolutePath(), test, instance);
                }
            }
        }
    }
    
    public static void processFile(String path, boolean test, CSV2RDF instance){
        if(test){
            instance.checkFile(path); 
        }else{
            instance.processFile(path);
        }
        
    }
    
    public static void main(String[] args){
        try{
//            String pathToInstancesDataFolder = "C:\\Users\\dgarijo\\Documents\\GitHub\\ModelCatalog\\Data";
            String pathToInstancesDataFolder = "C:\\Users\\dgarijo\\Documents\\GitHub\\ModelCatalog\\Data\\MINT";
//            String graph = "mint@isi.edu";//graph folder to load
            String graph = "texas@isi.edu";//graph folder to load
//            String pathToTransformationsDataFolder = "C:\\Users\\dgarijo\\Documents\\GitHub\\ModelCatalog\\Data\\Transformations";
            CSV2RDF catalog = new CSV2RDF("C:\\Users\\dgarijo\\Documents\\GitHub\\ModelCatalog\\Data\\Units\\dict.json", 
                    "C:\\Users\\dgarijo\\Documents\\GitHub\\ModelCatalog\\Data\\SVO\\variable-23-10-2019.ttl");
              //COVID models example
//            pathToInstancesDataFolder = "C:\\Users\\dgarijo\\Documents\\GitHub\\ModelCatalog\\Data\\COVID";
//              exportRDFFile("modelCatalogCovid.ttl", test.instances, "TTL");
              //END COVID
            processDataFolder(pathToInstancesDataFolder+"\\"+graph, false, catalog);
            exportRDFFile("modelCatalog_"+graph+".ttl", catalog.instances, "TTL");
            //exportRDFFile("modelCatalog.json", test.instances, "JSON-LD");
        }catch (Exception e){
            System.err.println("Error: "+e);
        }
    }
    
}

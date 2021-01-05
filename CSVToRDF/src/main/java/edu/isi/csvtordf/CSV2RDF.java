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
import java.util.ArrayList;
import org.apache.jena.datatypes.xsd.XSDDatatype;
import org.apache.jena.ontology.Individual;
import org.apache.jena.ontology.OntClass;
import org.apache.jena.ontology.OntModel;
import org.apache.jena.ontology.OntProperty;
import org.apache.jena.ontology.OntResource;
import org.apache.jena.query.*;
import org.apache.jena.rdf.model.Literal;
import org.apache.jena.rdf.model.ModelFactory;
import org.apache.jena.rdf.model.Property;
import org.apache.jena.vocabulary.XSD;

/**
 * @author dgarijo
 */
public class CSV2RDF {
    OntModel instances;
    OntModel variables;
    OntModel mcOntology;
    String instance_URI = "https://w3id.org/okn/i/mint/";
    JsonObject unitDictionary;
    
    /**
     * @param unitDictionaryFile File containing a dictionary between unit labels and their URIs.
     * @param scientificVariableFile  File containing the RDF extraction from GSN.
     */
    public CSV2RDF(String unitDictionaryFile, String scientificVariableFile) throws FileNotFoundException{
        instances = ModelFactory.createOntologyModel();
        variables = ModelFactory.createOntologyModel();
        //create class 
        instances.createClass("https://w3id.org/okn/o/sd/#SoftwareConfiguration");
        //we read all the variables separately, as we will use them to link contents.
        variables.read(scientificVariableFile);
        mcOntology = ModelFactory.createOntologyModel();
        mcOntology.read("https://w3id.org/okn/o/sdm#");
        mcOntology.read("https://w3id.org/okn/o/sd#");
        mcOntology.createObjectProperty("http://www.w3.org/2002/07/owl#sameAs");
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
        Individual mint_svo = instances.createClass("https://w3id.org/okn/o/sd#StandardVariable").createIndividual(instance_URI+encode(rowValue));
        mint_svo.addLabel(rowValue, null);
        //assign the variable to target node.
        ind.addProperty(p, mint_svo);
        /**
        read label, try to find one in the svo file (there should be).
        * If found, then copy description and label into instance, and add owl:sameAs.
        **/
        Query query = QueryFactory.create("select ?var ?desc where {"
               + "?var <http://www.w3.org/2000/01/rdf-schema#label> \""+rowValue+"\"" +
               "optional {?var <https://schema.org/description> ?desc}}");
        QueryExecution qe = QueryExecutionFactory.create(query, variables);
        ResultSet rs =  qe.execSelect();
        // if found in SVO, copy description and owl:sameAs
        if(rs.hasNext()){
            QuerySolution qs = rs.next();
            OntProperty pSameAs = (OntProperty)mcOntology.getProperty("http://www.w3.org/2002/07/owl#sameAs");
            mint_svo.addProperty(pSameAs, qs.getResource("?var"));
            Literal desc = qs.getLiteral("?desc");
            if (!"".equals(desc) && desc!= null){
                //svo comes with html tags. remove them
                mint_svo.addProperty(mcOntology.getOntProperty("https://w3id.org/okn/o/sd#description"),
                        desc.getString().replace("<p>","\n").replaceAll("\\<[^>]*>",""));
            }
         }
    }
    
    private void processFile(String path) throws Exception{
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
                                    OntResource range = p.getRange();
                                    if (range!=null && !range.isAnon()){
                                        switch (range.getURI()){
                                            case "http://www.w3.org/2001/XMLSchema#string":
                                                ind.addProperty(p, rowValue,XSDDatatype.XSDstring);
                                                break;
                                            case "http://www.w3.org/2001/XMLSchema#anyURI":
                                                if(rowValue.contains("http://") || rowValue.contains("https://")){
                                                    ind.addProperty(p, rowValue,XSDDatatype.XSDanyURI);
                                                }else{
                                                    System.err.println("ERROR: "+rowValue+" is not a URI. Ind: "+ind.getLocalName());
                                                }
                                                break;
                                            case "http://www.w3.org/2001/XMLSchema#integer":
                                                try{
                                                    Integer.parseInt(rowValue);
                                                    ind.addProperty(p, rowValue,XSDDatatype.XSDinteger);
                                                }catch (NumberFormatException e){
                                                    System.err.println("ERROR: "+rowValue+" is not an Integer. Ind: "+ind.getLocalName());
                                                }
                                                break;
                                            case "http://www.w3.org/2001/XMLSchema#float":
                                                try{
                                                    Float.parseFloat(rowValue);
                                                    ind.addProperty(p, rowValue,XSDDatatype.XSDfloat);
                                                }catch (NumberFormatException e){
                                                    System.err.println("ERROR: "+rowValue+" is not a float. Ind: "+ind.getLocalName());
                                                }
                                                break;
                                            default:
                                                //no xsd:string for labels, no needed.
                                                ind.addProperty(p, rowValue);
                                                break;
                                        }
                                    }else{
                                        //range is a union of ranges or no range declared. For now, leave as literal
                                        ind.addProperty(p, rowValue);
                                    }
                                    
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

        } catch (Exception e) {
            System.err.println("Error (likely the property has not been recognized) "+e.getMessage());
            //throw e;
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
    
    public static void processDataFolder(String path, boolean test, CSV2RDF instance)throws Exception{
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
    
    public static void processFile(String path, boolean test, CSV2RDF instance)throws Exception{
        if(test){
            instance.checkFile(path); 
        }else{
            instance.processFile(path);
        }
        
    }
    
    public static void main(String[] args){
        try{
//            String pathToInstancesDataFolder = "C:\\Users\\dgarijo\\Documents\\GitHub\\ModelCatalog\\Data";
//            String pathToTransformationsDataFolder = "C:\\Users\\dgarijo\\Documents\\GitHub\\ModelCatalog\\Data\\Transformations";

              //MINT
            String version = "1.6_to_1.7";
            // Unix
            String pathToGitFolder = "/home/dgarijo/Documents/GitHub/ModelCatalog";

            // WIN
            // String pathToGitFolder = "C:\\Users\\dgarijo\\Documents\\GitHub";
            String pathToInstancesDataFolder = pathToGitFolder+"/Data/MINT/"+version;
            String [] graphs = {"mint@isi.edu"};//, "texas@isi.edu", "coertel@mitre.org", "brandon@starsift.com","hvarg@isi.edu"};
              //end MINT

              //COVID models example
//            pathToInstancesDataFolder = "C:\\Users\\dgarijo\\Documents\\GitHub\\ModelCatalog\\Data\\COVID";
//            processDataFolder(pathToInstancesDataFolder, false, catalog);
//              exportRDFFile("modelCatalogCovid.ttl", catalog.instances, "TTL");
              //END COVID
              
              //wifire
//            String pathToInstancesDataFolder = "C:\\Users\\dgarijo\\Documents\\GitHub\\ModelCatalog\\Data\\Wifire";
//            String [] graphs = {"wifire@isi.edu"};
              //end wifire
            for (String graph:graphs){
                //a new catalog should be made per graph; otherwise graphs will be aggregated.
                CSV2RDF catalog = new CSV2RDF(pathToGitFolder+"/Data/Units/dict.json",
                        pathToGitFolder+"/Data/SVO/variable-23-10-2019.ttl");
                processDataFolder(pathToInstancesDataFolder+"/"+graph, false, catalog);
                exportRDFFile("modelCatalog_"+graph+"_"+version+".ttl", catalog.instances, "TTL");
            }
            System.out.println("Import process finished successfully");
        }catch (Exception e){
            System.err.println("Error: "+e);
        }
    }
    
}

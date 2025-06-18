from rdflib import Graph, Namespace
from decompose_sphn_by_concept  import decompose_labtestevents, decompose_diagnoses,decompose_drugprescriptions,decompose_medicalprocedures
from augment_sphn_hybrid import augment_graph
from pathlib import Path # add tp reqs


#### Script largely created with ChatGPT based on instructions how to decompose the initial file ### 

# Load RDF graph
g_original = Graph()
data_folder = Path(__file__).resolve().parent.parent / "data"
#data_folder = "../data/"
input_file = data_folder /"rdf_400_sphn.nt"
g_original.parse(input_file, format="nt")

# Namespaces
SPHN = Namespace("https://www.biomedit.ch/rdf/sphn-schema/sphn/")
KGEHR = Namespace("http://kg-representation-ehr.org/ontology/clinicalIntent#")
g_original.bind("sphn", SPHN)
g_original.bind("kgehr", KGEHR)

# Step 1: decompose nested LabTestEvent concept
g_labtestevent = decompose_labtestevents(input_graph=g_original)
print(len(g_labtestevent))
filename_decomposed = 'decomposed_sphn_complete_hybrid_labtestevent.ttl'
g_labtestevent.serialize(destination=data_folder / filename_decomposed, format = 'turtle')

# Step 2: decompose nested Diagnosis concept
g_original_diagnosis = Graph()
#data_folder = "./data/"
input_file = data_folder /"rdf_400_sphn.nt"
g_original_diagnosis.parse(input_file, format="nt")

g_diagnosis= decompose_diagnoses(input_graph=g_original_diagnosis)
print(len(g_diagnosis))
filename_decomposed = 'decomposed_sphn_complete_hybrid_diagnosis.ttl'
g_diagnosis.serialize(destination=data_folder / filename_decomposed, format = 'turtle')


# Step 3: decompose nested Drugprescription concept
g_original_drugprescription = Graph()
#data_folder = "./data/"
input_file = data_folder /"rdf_400_sphn.nt"
g_original_drugprescription.parse(input_file, format="nt")

g_drugprescription= decompose_drugprescriptions(input_graph=g_original_drugprescription)
print(len(g_drugprescription))
filename_decomposed = 'decomposed_sphn_complete_hybrid_drugprescription.ttl'
g_drugprescription.serialize(destination=data_folder / filename_decomposed, format = 'turtle')

# Step 4: decompose nested MedicalProcedure concept
g_original_medicalproc = Graph()
#data_folder = "./data/"
input_file = data_folder / "rdf_400_sphn.nt"
g_original_medicalproc.parse(input_file, format="nt")

g_medicalprocedure= decompose_medicalprocedures(input_graph=g_original_medicalproc)
print(len(g_medicalprocedure))
filename_decomposed = 'decomposed_sphn_complete_hybrid_medicalproc.ttl'
g_medicalprocedure.serialize(destination=data_folder / filename_decomposed, format = 'turtle')

g_merged = Graph()

# Merge all graphs
g_merged += g_medicalprocedure
g_merged += g_drugprescription
g_merged += g_diagnosis
g_merged += g_labtestevent

g_merged.serialize(destination=data_folder / "merged_sphn_decomposed.ttl", format="turtle")

# Step 5: Augment the graph 
augment_graph(g_merged)

# Serialize to file
output_path = data_folder / "rdf_400_sphn_augmented_hybrid-18062025.ttl"
g_merged.serialize(destination=output_path, format="turtle")

print(f"Augmented RDF saved to: {output_path}")


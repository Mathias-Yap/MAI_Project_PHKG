from rdflib import Graph, URIRef, BNode, Literal, Namespace, RDF
import uuid

#### Script largely created with ChatGPT based on instructions how to decompose the initial file ### 

# Namespaces
SPHN = Namespace("https://www.biomedit.ch/rdf/sphn-schema/sphn/")
KGEHR = Namespace("http://kg-representation-ehr.org/ontology/clinicalIntent#")

def make_uuid_uri(base):
    return URIRef(str(base) + "/" + str(uuid.uuid4()))

def generate_uri(concept_type: str) -> URIRef:
    return URIRef(f"{KGEHR}{concept_type}/{uuid.uuid4()}")

def decompose_labtestevents(input_graph: Graph) -> Graph:
    """
    Decomposes nested LabTestEvent and LabResult structures into flat triples using UUIDs for LabResult.
    Returns a new RDFLib Graph.
    """
    output_graph = Graph()
    output_graph.bind("sphn", SPHN)
    output_graph.bind("kgehr", KGEHR)

    for lab_event, _, _ in input_graph.triples((None, RDF.type, SPHN.LabTestEvent)):
        # Copy patient reference and assign Patient type
        for _, _, patient in input_graph.triples((lab_event, SPHN.hasSubjectPseudoIdentifier, None)):
            output_graph.add((lab_event, SPHN.hasSubjectPseudoIdentifier, patient))
            output_graph.add((patient, RDF.type, SPHN.Patient))

        # Handle nested LabResult
        for _, _, nested_result in input_graph.triples((lab_event, SPHN.hasLabTest, None)):
            for _, _, code in input_graph.triples((nested_result, SPHN.hasCode, None)):
                lab_result_uri = make_uuid_uri(SPHN.LabResult)
                output_graph.add((lab_event, SPHN.hasLabResult, lab_result_uri))
                output_graph.add((lab_result_uri, SPHN.hasCode, code))
                output_graph.add((code, RDF.type, SPHN.LabResult))

    return output_graph

def decompose_diagnoses(input_graph: Graph) -> Graph:
    g_out = Graph()
    g_out.bind("sphn", SPHN)
    g_out.bind("kgehr", KGEHR)

    for diagnosis in input_graph.subjects(RDF.type, SPHN.Diagnosis):
        patient = input_graph.value(diagnosis, SPHN.hasSubjectPseudoIdentifier)
        code = input_graph.value(diagnosis, SPHN.hasCode)

        diagnosis_node = generate_uri("Diagnosis")
        code_node = generate_uri("Code")

        g_out.add((patient, SPHN.hasDiagnosis, diagnosis_node))
        g_out.add((diagnosis_node, RDF.type, SPHN.Diagnosis))
        g_out.add((diagnosis_node, SPHN.hasCode, code_node))
        g_out.add((code_node, RDF.type, SPHN.Code))
        g_out.add((code_node, SPHN.hasCodeValue, code))

    return g_out

def decompose_drugprescriptions(input_graph: Graph) -> Graph:
    g_out = Graph()
    g_out.bind("sphn", SPHN)
    g_out.bind("kgehr", KGEHR)

    for dp in input_graph.subjects(RDF.type, SPHN.DrugPrescription):
        patient = input_graph.value(dp, SPHN.hasSubjectPseudoIdentifier)
        drug = input_graph.value(dp, SPHN.hasDrug)

        if not (patient and drug):
            continue  # skip if key data missing

        substance = input_graph.value(drug, SPHN.hasActiveIngredient)
        if not substance:
            continue  # skip if nested concept missing

        code = input_graph.value(substance, SPHN.hasCode)
        if not code:
            continue  # skip if code missing

        # Create fresh URIs
        dp_node = generate_uri("DrugPrescription")
        sub_node = generate_uri("Substance")
        drug_node = generate_uri("Drug")

        # Add flattened triples
        g_out.add((patient, KGEHR.hasDrugPrescription, dp_node))
        g_out.add((dp_node, RDF.type, SPHN.DrugPrescription))
        g_out.add((dp_node, SPHN.hasDrug, drug_node))
        g_out.add((drug_node, RDF.type, SPHN.Drug))
        g_out.add((drug_node, SPHN.hasActiveIngredient, sub_node))
        g_out.add((sub_node, RDF.type, SPHN.Substance))
        g_out.add((sub_node, SPHN.hasCode, code))

    return g_out
def decompose_medicalprocedures(input_graph: Graph) -> Graph:
    g_out = Graph()
    g_out.bind("sphn", SPHN)
    g_out.bind("kgehr", KGEHR)

    for mp in input_graph.subjects(RDF.type, SPHN.MedicalProcedure):
        patient = input_graph.value(mp, SPHN.hasSubjectPseudoIdentifier)
        code = input_graph.value(mp, SPHN.hasCode)

        mp_node = generate_uri("MedicalProcedure")
        code_node = generate_uri("Code")

        g_out.add((patient, KGEHR.hasMedicalProcedure, mp_node))
        g_out.add((mp_node, RDF.type, SPHN.MedicalProcedure))
        g_out.add((mp_node, SPHN.hasCode, code_node))
        g_out.add((code_node, RDF.type, SPHN.Code))
        g_out.add((code_node, SPHN.hasCodeValue, code))

    return g_out

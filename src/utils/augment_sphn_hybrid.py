from rdflib import Graph, Namespace, RDF, Literal, URIRef, XSD
import uuid
from datetime import datetime, timedelta
import random

#### Script largely created with ChatGPT based on instructions how to decompose the initial file ### 

SPHN = Namespace("https://www.biomedit.ch/rdf/sphn-schema/sphn/")
KGEHR = Namespace("http://kg-representation-ehr.org/ontology/clinicalIntent#")

def generate_uri(entity_type):
    return URIRef(f"http://kg-representation-ehr.org/ontology/clinicalIntent#{entity_type}/{uuid.uuid4()}")

def random_decimal(min_val=2.0, max_val=8.5):
    return round(random.uniform(min_val, max_val), 1)

def random_date(start=datetime(2023, 1, 1), end=datetime(2024, 6, 1)):
    delta = end - start
    return start + timedelta(days=random.randint(0, delta.days))

def augment_graph(g: Graph) -> Graph:
    for lab_event in g.subjects(RDF.type, SPHN.LabTestEvent):
        lab_result = g.value(subject=lab_event, predicate=SPHN.hasLabResult)
        if not lab_result:
            lab_result = generate_uri("LabResult")
            g.add((lab_event, SPHN.hasLabResult, lab_result))
            g.add((lab_result, RDF.type, SPHN.LabResult))
            g.add((lab_result, SPHN.hasQuantityValue, Literal(random_decimal(), datatype=XSD.decimal)))

    for dp in g.subjects(RDF.type, SPHN.DrugPrescription):
        drug = g.value(subject=dp, predicate=SPHN.hasDrug)
        if not drug:
            drug = generate_uri("Drug")
            g.add((dp, SPHN.hasDrug, drug))
            g.add((drug, RDF.type, SPHN.Drug))

        substance = g.value(subject=drug, predicate=SPHN.hasActiveIngredient)
        if not substance:
            substance = generate_uri("Substance")
            g.add((drug, SPHN.hasActiveIngredient, substance))
            g.add((substance, RDF.type, SPHN.Substance))

        code = g.value(subject=substance, predicate=SPHN.hasCode)
        if not code:
            dummy_code = URIRef("https://www.biomedit.ch/rdf/sphn-schema/sphn/ndc#00000000000")
            g.add((substance, SPHN.hasCode, dummy_code))

    for diag in g.subjects(RDF.type, SPHN.Diagnosis):
        if not any(g.objects(subject=diag, predicate=SPHN.hasCode)):
            dummy_code = URIRef("https://www.biomedit.ch/rdf/sphn-schema/sphn/icd#Z999")
            g.add((diag, SPHN.hasCode, dummy_code))

    for proc in g.subjects(RDF.type, SPHN.MedicalProcedure):
        if not any(g.objects(subject=proc, predicate=SPHN.hasCode)):
            dummy_code = URIRef("https://www.biomedit.ch/rdf/sphn-schema/sphn/icd#0UNKNOWN")
            g.add((proc, SPHN.hasCode, dummy_code))

    return g

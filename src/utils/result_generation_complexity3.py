# Fix and simplify the script logic to relax conditions and ensure entries are created
from rdflib import Graph, URIRef, Literal
import pandas as pd
import os

# Parameters
sample_size = 100
rdf_path = f"../data/rdf_{sample_size}_sphn.nt"
output_dir = f"../sparql_queries/midterm_experiment_queries/labtest_values_compl_three/size_{sample_size}/"
os.makedirs(output_dir, exist_ok=True)

# Namespaces
NS = "https://www.biomedit.ch/rdf/sphn-schema/sphn/"
has_subject = URIRef(NS + "hasSubjectPseudoIdentifier")
has_labtest = URIRef(NS + "hasLabTest")
has_code = URIRef(NS + "hasCode")

# Load graph
g = Graph()
g.parse(rdf_path, format="turtle")

# Helper to extract last part of URI or string literal
def get_label(val):
    if isinstance(val, Literal):
        return str(val)
    return str(val).split("/")[-1]

records = []

# Traverse the graph with loosened conditions (only require hasCode on LabResult)
for lab_test, _, patient in g.triples((None, has_subject, None)):
    for _, _, lab_result in g.triples((lab_test, has_labtest, None)):
        for _, _, lab_code in g.triples((lab_result, has_code, None)):

            # Check if patient has a DrugPrescription
            for drug_prescription, _, p2 in g.triples((None, has_subject, patient)):
                if "DrugPrescription" in str(drug_prescription):

                    patient_label = get_label(patient)
                    lab_code_label = get_label(lab_code)

                    question = (
                        f"What was the code of a test recorded for patient {patient_label}, "
                        f"who also had a DrugPrescription?"
                    )

                    sparql = f"""PREFIX sphn: <{NS}>
                        SELECT ?labCode WHERE {{
                        <{lab_test}> sphn:hasSubjectPseudoIdentifier <{patient}> ;
                                    sphn:hasLabTest <{lab_result}> .
                        <{lab_result}> sphn:hasCode ?labCode .
                        <{drug_prescription}> sphn:hasSubjectPseudoIdentifier <{patient}> .
                        }}"""
                    
                    results = g.query(sparql)
                    # Extract the first result (if any)
                    answer = None
                    for row in results:
                        if row.labels:
                            var_name = list(row.labels)[0]
                            ##var_name = row.labels[0]  # assuming you only SELECT one variable
                            answer = str(row[var_name])
                            answer2= get_label(row['labCode'])
                            break

                    sparql_filename = os.path.join(
                        output_dir,
                        f"query_combined_{sample_size}_{len(records):03}.sparql"
                    )
                    with open(sparql_filename, "w") as f:
                        f.write(sparql.strip() + "\n")
        
                    # Append to records for CSV
                    records.append({
                        #"query_file": sparql_filename,
                        "answer":answer2 ,##get_label(answer) or "NO RESULT"
                        "query": sparql.strip()
                    
                    })

                    

# Save results to CSV
csv_path = os.path.join(output_dir, f"labtest_value_queries_{sample_size}.csv")
pd.DataFrame(records).to_csv(csv_path, index=False,  lineterminator='\n')

csv_path, len(records)
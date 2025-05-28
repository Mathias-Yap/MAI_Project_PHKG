from io import StringIO
from rdflib import Graph, URIRef, Literal
import os
import pandas as pd

g = Graph()

##g.parse(r'/content/drive/MyDrive/RDF files/rdf_100_sphn.txt', format="turtle")


sample_size = 400
rdf_path = f"../data/rdf_{sample_size}_sphn.txt"
output_dir = f"../../sparql_queries/midterm_experiment_queries/sparql_queries_shape_compl_two/size_{sample_size}/"
os.makedirs(output_dir, exist_ok=True)
g.parse(rdf_path, format="turtle")
print(f"Graph has {len(g)} statements.")


# Namespaces
NS = "https://www.biomedit.ch/rdf/sphn-schema/sphn/"
has_subject = URIRef(NS + "hasSubjectPseudoIdentifier")
has_code = URIRef(NS + "hasCode")
has_labtest = URIRef(NS + "hasLabTest")

# Helper
def get_label(val):
    if isinstance(val, Literal):
        return str(val)
    return str(val).split("/")[-1] if isinstance(val, URIRef) else str(val)

records = []

# Process each LabTestEvent (subject linked to patient)
for lab_event, _, patient in g.triples((None, has_subject, None)):
    for _, _, lab_result in g.triples((lab_event, has_labtest, None)):
        for _, _, code in g.triples((lab_result, has_code, None)):
            patient_label = get_label(patient)
            code_label = get_label(code)
            lab_event_str = str(lab_event)

            question = f"What test with code {code_label} was recorded for patient {patient_label} in LabTestEvent?"
            sparql = f"""PREFIX sphn: <{NS}>
                SELECT ?code WHERE {{
                <{lab_event_str}> sphn:hasSubjectPseudoIdentifier <{patient}> ;
                                    sphn:hasLabTest ?labResult .
                ?labResult sphn:hasCode ?code .
                }}"""

            ##records.append({
               ## "question": question,
                ##"answer": code_label,
                ##"sparql": sparql.strip()
            ##})

            # Save each SPARQL query to its own file
            sparql_filename = os.path.join(
                output_dir,
                f"query_event_patient_{sample_size}_{len(records):03}.sparql"
            )


            results = g.query(sparql)
              # Extract the first result (if any)
            answer = None
            for row in results:
                if row.labels:
                    var_name = list(row.labels)[0]
                    ##var_name = row.labels[0]  # assuming you only SELECT one variable
                    answer = str(row[var_name])
                    answer2= get_label(row['code'])
                    break  # just take the first match
            with open(sparql_filename, "w") as f:
                f.write(sparql.strip() + "\n")
   
            # Append to records for CSV
            records.append({
                #"query_file": sparql_filename,
                "answer":answer2 ,##get_label(answer) or "NO RESULT"
                "query": sparql.strip()
               
            })

# Save all records to CSV
csv_path = f"{output_dir}/labtestevent_queries_{sample_size}.csv"
pd.DataFrame(records).to_csv(csv_path, index=False)

print("✅ SPARQL generation complete.")
print("CSV:", csv_path)
print("Folder:", output_dir)
print(f"SPARQL queries saved in: {output_dir}")




## QUERY sample sparqls
# Test query against known valid triple
query_result = """
PREFIX sphn: <https://www.biomedit.ch/rdf/sphn-schema/sphn/>
SELECT ?code WHERE {
  <https://www.biomedit.ch/rdf/sphn-schema/sphn/LabTestEvent/1/patients/19164956> sphn:hasLabTest ?labResult .
  ?labResult sphn:hasCode ?code .
}

"""

results = g.query(query_result)

# Output results
for row in results:
    print(f"code: {get_label(row['code'])}")
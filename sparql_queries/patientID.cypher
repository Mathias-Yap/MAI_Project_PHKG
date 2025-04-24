MATCH (patient:DrugPrescription {id: "18533998"})-[:HAS_DRUG]->(drug)
RETURN drug

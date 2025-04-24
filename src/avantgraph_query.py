from neo4j import GraphDatabase

def connect_to_neo4j():
    uri = "bolt://localhost:7687"  # Replace with your Neo4j host and port
    driver = GraphDatabase.driver(uri)
    query = """
    WITH SPARQL "
    SELECT *
    WHERE { ?s ?p ?o . }
    LIMIT 100 "
    """
    session = driver.session()
    result = session.run(query)
    return result

result = connect_to_neo4j()
print("hello?")
for record in result:
    print(record)
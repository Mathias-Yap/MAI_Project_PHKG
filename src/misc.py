def get_ontology_from_triples():
    import os
    from rdflib import Graph, RDF, OWL

    # Make sure the results directory exists
    os.makedirs("results", exist_ok=True)

    # Build the path to the RDF file relative to this script's location
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    data_path = os.path.join(base_dir, "data", "rdf_400_sphn.txt")
    print(f"Loading RDF data from: {data_path}")

    # Load the RDF graph
    g = Graph()
    g.parse(data_path, format="nt")

    # Inferred classes: anything used as a rdf:type
    inferred_classes = set(o for s, p, o in g.triples((None, RDF.type, None)))

    # Inferred properties: all unique predicates
    inferred_properties = set(p for s, p, o in g)

    # Split inferred properties into likely object and datatype properties
    inferred_object_props = set()
    inferred_datatype_props = set()

    for prop in inferred_properties:
        # Very rough heuristic: if the object is a URI, assume object property
        for s, p, o in g.triples((None, prop, None)):
            if isinstance(o, (str, int, float)):
                inferred_datatype_props.add(prop)
            else:
                inferred_object_props.add(prop)
            break  # one sample is enough


    # Save inferred vocabulary
    with open("results/vocabulary_rdf_400_sphn.txt", "w", encoding="utf-8") as f:
        f.write("=== INFERRED CLASSES (via rdf:type) ===\n")
        for cls in inferred_classes:
            f.write(f"{cls}\n")

        f.write("\n=== INFERRED OBJECT PROPERTIES ===\n")
        for prop in inferred_object_props:
            f.write(f"{prop}\n")

        f.write("\n=== INFERRED DATATYPE PROPERTIES ===\n")
        for prop in inferred_datatype_props:
            f.write(f"{prop}\n")

    print("Vocabulary written to results/vocabulary.txt")


if __name__ == "__main__":
    get_ontology_from_triples()

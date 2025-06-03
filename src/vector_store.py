"""Creation of and interaction with vector store."""

import os


import spacy
from langchain_community.vectorstores import FAISS, DistanceStrategy
from langchain_huggingface import HuggingFaceEmbeddings
from rdflib import Graph, URIRef, RDF, RDFS, OWL, XSD
from typing import Tuple


from utils.graph import load_graph

src_dir = os.path.dirname(os.path.dirname(__file__))
vector_store_class = os.path.join(src_dir, "vector_stores/classes.index")


model_name: str = "mixedbread-ai/mxbai-embed-large-v1"


def get_classes(graph: Graph) -> Tuple[list[dict], list[str]]:
    """
    Extracts class metadata and ontology-defined relationships (via rdfs:domain and rdfs:range).
    Returns:
        Tuple of metadata dicts and textual summaries.
    """

    def get_label(node):
        return str(graph.value(node, RDFS.label)) if node else None

    # Precompute all object and datatype properties and their domains/ranges
    prop_info = []
    for prop_type in [OWL.ObjectProperty, OWL.DatatypeProperty]:
        for prop in graph.subjects(RDF.type, prop_type):
            domains = list(graph.objects(prop, RDFS.domain))
            ranges = list(graph.objects(prop, RDFS.range))

            for domain in domains:
                for range_ in ranges:
                    prop_info.append(
                        (
                            prop,
                            get_label(prop),
                            domain,
                            get_label(domain),
                            range_,
                            get_label(range_)
                            if prop_type == OWL.ObjectProperty
                            else str(range_),
                        )
                    )

    # Map classes and collect relevant data
    metadatas = []
    text_representations = []

    class_nodes = set(graph.subjects(RDF.type, OWL.Class))

    for class_node in class_nodes:
        class_label = get_label(class_node)
        comment = graph.value(class_node, RDFS.comment)
        relations = set()

        for prop, prop_label, domain, domain_label, range_, range_label in prop_info:
            if prop_label is None:
                continue

            if domain == class_node:
                relations.add(f"{domain_label} -> {prop_label} -> {range_label}")
            if range_ == class_node:
                relations.add(f"{domain_label} -> {prop_label} -> {range_label}")

        metadatas.append(
            {
                "uri": str(class_node),
                "label": class_label,
                "comment": str(comment) if comment else None,
                "relations": sorted(relations),
            }
        )

        if class_label or comment:
            text = f"Class: {class_label}\nDescription: {comment}"
            if relations:
                text += "\nRelations:\n" + "\n".join(sorted(relations))
            text_representations.append(text)

    return metadatas, text_representations


class VectorStore:
    """Vector store class for creating and loading vector stores."""

    def __init__(self, file_name: str | None = None):
        """Initialize the vector store with the specified file name."""

        # Load the HuggingFace embeddings model
        self.encoder = HuggingFaceEmbeddings(
            model_name=model_name, model_kwargs={"device": "cpu"}
        )  # TODO: Ideally use GPU with multi_process=True, but for our laptop, we use a CPU for simplicity

        # Create or load the vector store based on the provided file name
        self.vector_store = (
            self.create_vector_store(load_graph("ontology"))
            if file_name is None
            else self.load_vector_store(file_name)
        )

        # Initialize the NLP model for text processing
        def load_nlp_model(model):
            try:
                nlp = spacy.load(model)
            except OSError:
                print(f"Downloading model: {model}")
                spacy.cli.download(model)
                nlp = spacy.load(model)
            return nlp

        self.nlp = load_nlp_model("en_core_web_trf")

    def create_vector_store(self, ontology: Graph) -> None:
        """
        Create a vector store from the specified graph.

        Args:
            ontology (Graph): The graph object to create the vector store from.
        """
        metadatas, text_representations = get_classes(ontology)

        # Create a vector store from the text representations and metadata
        vector_store = FAISS.from_texts(
            text_representations,
            self.encoder,
            metadatas,
        )

        # Save the vector store as a FAISS index
        vector_store.save_local(vector_store_class)

        return vector_store

    def load_vector_store(self, file_name: str) -> FAISS:
        """
        Load the vector store from the specified file(s).

        Args:
            file_name (str): The name of the file to load the vector store from, either classes/predicates.

        Returns:
            FAISS: The loaded vector store.
        """
        # Load the vector store from the specified files
        vector_store = FAISS.load_local(
            os.path.join(src_dir, f"vector_stores/{file_name}.index"),
            self.encoder,
            allow_dangerous_deserialization=True,
        )

        return vector_store

    def query(
        self, query: str, threshold: int = 200, k: int = 1, debug: bool = False
    ) -> list[dict]:
        """
        Retrieve relevant nodes from the vector store based on the query.

        Args:
            query (str): The query string to search for relevant classes.

        Returns:
            list[dict]: A list of dictionaries containing relevant class metadata.
        """

        def extract_concepts(query: str) -> list[str]:
            doc = self.nlp(query)
            return [chunk.text for chunk in doc.noun_chunks]

        hits = set()

        for concept in extract_concepts(query):
            results = self.vector_store.similarity_search_with_score(concept, k=k)
            for result, score in results:
                if score <= threshold:
                    if debug:
                        print(
                            f"Concept: {concept}, Score: {score}, Metadata: {result.metadata}"
                        )
                    hits.add(result.metadata["uri"])

        return hits


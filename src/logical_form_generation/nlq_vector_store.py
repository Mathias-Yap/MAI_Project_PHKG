"""Creation of and interaction with question template vector store."""

import os
import re
from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings
from typing import List, Dict, Tuple, Optional, Set
import yaml

src_dir = os.path.dirname(os.path.dirname(__file__))
vector_store_questions = os.path.join(src_dir, "vector_stores/questions.index")

model_name: str = "mixedbread-ai/mxbai-embed-large-v1"


class QuestionTemplateVectorStore:
    """Vector store class for creating and loading question template vector stores."""

    def __init__(self, file_name: str | None = None, qq_data: List[Dict] | None = None, yaml_file: str | None = None):
        """
        Initialize the question template vector store.

        Natural language question templates must have placeholders in the form of {placeholder} (e.g., {substance}, {patient_id}),
        SPARQL query templates must have placeholders in the form of {{placeholder}} (e.g., {{substance_uri}}, {{patient_uri}}).
        
        Args:
            file_name (str, optional): Name of existing vector store file to load
            qq_data (List[Dict], optional): List of Dictionaries containing question/query templates:
                [{'question_template': str, 'query_template': str}, ...]
            yaml_file (str, optional): Path to YAML file containing question templates
        """
        
        # Load the HuggingFace embeddings model
        self.encoder = HuggingFaceEmbeddings(
            model_name=model_name, model_kwargs={"device": "cpu"}
        )  # TODO: Ideally use GPU with multi_process=True, but for our laptop, we use a CPU for simplicity

        # Create or load the vector store based on the provided parameters
        if file_name is not None:
            self.vector_store = self.load_vector_store(file_name)
        elif yaml_file is not None:
            with open(yaml_file, 'r') as file:
                question_templates = yaml.safe_load(file)
                # If the YAML file contains keys "Question" and "Query", rename them to "question_template" and "query_template"
                for template in question_templates:
                    if "Question" in template:
                        template["question_template"] = template.pop("Question")
                    if "Query" in template:
                        template["query_template"] = template.pop("Query")
                self.vector_store = self.create_vector_store(question_templates)
        elif qq_data is not None:
            self.vector_store = self.create_vector_store(qq_data)
        else:
            raise ValueError("Either file_name, qq_data, or yaml_file must be provided")

    def extract_nlq_placeholders(self, text: str) -> List[str]:
        """
        Extract placeholder types from a natural language text string.
        
        Args:
            text (str): The natural language text to extract placeholders from
            
        Returns:
            List[str]: List of extracted placeholder types
        """
        # Find all occurrences of {placeholder} in the text
        matches = re.findall(r"\{([^{}]+)\}", text)
        # Remove trailing digits and convert to lowercase
        placeholders = [re.sub(r"\d+$", "", m).lower() for m in matches]
        return placeholders
    
    def extract_sparql_placeholders(self, text: str) -> List[str]:
        """
        Extract SPARQL placeholder types from a text string.
        
        Args:
            text (str): The SPARQL query text to extract placeholders from

        Returns:
            List[str]: List of extracted placeholder types
        """
        # Match patterns like {{placeholder}} and return the placeholder names
        matches = re.findall(r"\{\{([^{}]+)\}\}", text)
        # Remove trailing digits and convert to lowercase
        placeholders = [re.sub(r"\d+$", "", m).lower() for m in matches]
        return placeholders

    def create_vector_store(self, question_templates: List[Dict]) -> FAISS:
        """
        Create a vector store from the specified question templates.

        Args:
            question_templates (List[Dict]): List of dictionaries containing question and query templates
                Expected format: [{'question_template': str, 'query_template': str}, ...]

        Returns:
            FAISS: The created vector store
        """
        if not question_templates:
            raise ValueError("question_templates cannot be empty")

        # Extract question templates for text representation
        text_representations = []
        metadatas = []

        for i, template_pair in enumerate(question_templates):
            if 'question_template' not in template_pair or 'query_template' not in template_pair:
                raise ValueError(f"Template at index {i} missing required keys 'question_template' or 'query_template'")
            
            question_template = template_pair['question_template']
            query_template = template_pair['query_template']
            
            # Use the question template as the text representation for embedding
            text_representations.append(question_template)
            
            # Store only question, query and their placeholders in metadata
            metadatas.append({
                'question_template': question_template,
                'query_template': query_template,
                'question_placeholders': self.extract_nlq_placeholders(question_template),
                'query_placeholders': self.extract_sparql_placeholders(query_template)
            })

        # Create a vector store from the question templates and metadata
        vector_store = FAISS.from_texts(
            text_representations,
            self.encoder,
            metadatas,
        )

        # Save the vector store as a FAISS index
        vector_store.save_local(vector_store_questions)

        return vector_store

    def load_vector_store(self, file_name: str) -> FAISS:
        """
        Load the vector store from the specified file.

        Args:
            file_name (str): The name of the file to load the vector store from.

        Returns:
            FAISS: The loaded vector store.
        """
        # Load the vector store from the specified file
        vector_store = FAISS.load_local(
            os.path.join(src_dir, f"vector_stores/{file_name}.index"),
            self.encoder,
            allow_dangerous_deserialization=True,
        )

        return vector_store

    def query(
        self, 
        query: str, 
        threshold: int = 200,
        k: int = 3, 
        debug: bool = False
    ) -> List[Dict]:
        """
        Retrieve relevant question templates from the vector store based on the query.

        Args:
            query (str): The natural language query to match against question templates
            threshold (float): Similarity threshold (lower is more similar for cosine similarity)
            k (int): Number of top results to return
            debug (bool): Whether to print debug information

        Returns:
            List[Dict]: A list of dictionaries containing relevant template metadata
        """
        # Search for similar question templates
        results = self.vector_store.similarity_search_with_score(query, k=k)  # Get more to allow for filtering
        
        matched_templates = []
        
        for result, score in results:
            # Check similarity threshold
            if score <= threshold:
                query_placeholders = result.metadata.get('query_placeholders', [])
                question_placeholders = result.metadata.get('question_placeholders', [])
                template_info = {
                    'question_template': result.metadata['question_template'],
                    'query_template': result.metadata['query_template'],
                    'question_placeholders': question_placeholders,
                    'query_placeholders': query_placeholders,
                    'similarity_score': score
                }
                
                if debug:
                    print(f"Query: {query}")
                    print(f"Matched Question: {result.metadata['question_template']}")
                    print(f"Query Template: {result.metadata['query_template']}")
                    print(f"Question Placeholders: {question_placeholders}")
                    print(f"Query Placeholders: {query_placeholders}")
                    print(f"Score: {score}")
                    print("-" * 50)
                
                matched_templates.append(template_info)
            
        
        return matched_templates

    def get_best_match(
        self, 
        query: str, 
        debug: bool = False
    ) -> Optional[Dict]:
        """
        Get the single best matching template for a query.

        Args:
            query (str): The natural language query
            filter_question_placeholders (List[str], optional): Filter by question placeholder types
            filter_query_placeholders (List[str], optional): Filter by query placeholder types
            debug (bool): Whether to print debug information

        Returns:
            Dict or None: The best matching template metadata, or None if no good match
        """
        matches = self.query(
            query, 
            k=1, 
            debug=debug
        )
        return matches[0] if matches else None

    def list_all_templates(
        self, 
        filter_question_placeholders: Optional[List[str]] = None, 
        filter_query_placeholders: Optional[List[str]] = None
    ) -> List[Dict]:
        """
        Get all stored question templates, optionally filtered by placeholders.

        Args:
            filter_question_placeholders (List[str], optional): Filter by question placeholder types
            filter_query_placeholders (List[str], optional): Filter by query placeholder types

        Returns:
            List[Dict]: All stored template metadata (filtered if specified)
        """
        # Get all documents in the vector store
        all_docs = self.vector_store.similarity_search("", k=self.vector_store.index.ntotal)
        
        templates = []
        for i, doc in enumerate(all_docs):
            question_placeholders = doc.metadata.get('question_placeholders', [])
            query_placeholders = doc.metadata.get('query_placeholders', [])
            
            # Apply filters if provided
            if filter_question_placeholders:
                if not any(placeholder in question_placeholders for placeholder in filter_question_placeholders):
                    continue
            
            if filter_query_placeholders:
                if not any(placeholder in query_placeholders for placeholder in filter_query_placeholders):
                    continue
            
            templates.append({
                'question_template': doc.metadata['question_template'],
                'query_template': doc.metadata['query_template'],
                'question_placeholders': question_placeholders,
                'query_placeholders': query_placeholders,
                'template_id': i
            })
        
        return templates

# Example usage and helper functions
def create_sample_templates() -> List[Dict]:
    """
    Create sample question/query template pairs for testing.
    Uses {placeholder} for natural language and {{placeholder}} for SPARQL.
    
    Returns:
        List[Dict]: Sample templates
    """
    return [
        {
            'question_template': "How many patients have {x.type} {x.value}",
            'query_template': "SELECT ?definition WHERE { {{substance_uri}} rdfs:comment ?definition }"
        },
        {   'question_template': "How many patients have {x.type} {x.value} that contains {y.type} {y.value}",       
            'query_template': "SELECT ?definition WHERE { {{substance_uri}} rdfs:comment ?definition . {{substance_uri}} :contains {{substance2_uri}} }"
        }
        # {
        #     'question_template': "What are the properties of {patient}?",
        #     'query_template': "SELECT ?property WHERE { ?property rdfs:domain {{patient_uri}} }"
        # },
        # {
        #     'question_template': "What treatments are available for {patient}?",
        #     'query_template': "SELECT ?treatment WHERE { {{patient_uri}} :hasTreatment ?treatment }"
        # },
        # {
        #     'question_template': "How many {substance} samples are there?",
        #     'query_template': "SELECT (COUNT(?sample) as ?count) WHERE { ?sample rdf:type {{substance_uri}} }"
        # },
        # {
        #     'question_template': "What is the dosage for {substance}?",
        #     'query_template': "SELECT ?dosage WHERE { {{substance_uri}} :hasDosage ?dosage }"
        # },
        # {
        #     'question_template': "What is the interaction between {substance1} and {substance2}?",
        #     'query_template': "SELECT ?interaction WHERE { {{substance1_uri}} :interactsWith {{substance2_uri}} . {{substance1_uri}} :hasInteraction ?interaction }"
        # }
    ]


if __name__ == "__main__":
    # Example usage
    sample_templates = create_sample_templates()
     
    # Create a new vector store with sample templates
    question_store = QuestionTemplateVectorStore(yaml_file = "/home/mathiasyap/Code/university/phkg/MAI_Project_PHKG/sparql_queries/question_query_templates.yaml")
    
    # Query for similar questions
    test_query ="List all medical procedures performed on patient 120356"
    
    # Query without filters
    all_matches = question_store.query(test_query, debug=True)
    print(f"Found {len(all_matches)} total matches for: '{test_query}'")
    print()
    
    # Query filtered by question placeholder type
    substance_matches = question_store.query(
        test_query, 
        debug=True
    )
    print(f"Found {len(substance_matches)} query matches for: '{test_query}'")
    print()
    print("Substance Matches:")
    for match in substance_matches:
        print(f"Question: {match['question_template']}")
        print(f"Query: {match['query_template']}")
        print(f"Placeholders: {match['question_placeholders']}, {match['query_placeholders']}")
        print(f"Score: {match['similarity_score']}")
        print("-" * 50)
    
    # Show all templates with placeholders
    all_templates = question_store.list_all_templates()
    print(f"\nAll templates ({len(all_templates)}):")
    for template in all_templates:
        print(f"ID {template['template_id']}: {template['question_template']}")
        print(f"  Question placeholders: {template['question_placeholders']}")
        print(f"  Query placeholders: {template['query_placeholders']}")
        print()
import os
from rdflib import Graph
from . import pipeline_stages
from .llm import llm_pipeline
from pipeline.llm.gpt_pipeline import gpt_pipeline
from utils.graph import load_graph
import json


INITIAL_PROMPT = """
Task: Generate a SPARQL SELECT statement for querying a graph database.
Question: Which patients have been diagnosed with I427?
Answer:
```
PREFIX sphn: <https://www.biomedit.ch/rdf/sphn-schema/sphn/>
PREFIX icd: <https://www.biomedit.ch/rdf/sphn-schema/sphn/icd#>

SELECT ?patient WHERE {{
  ?patient sphn:hasDiagnosis ?diag .
  ?diag sphn:hasCode ?code .
  ?code sphn:hasCodeValue
         icd:I427 .
}}
```
Keep in mind that you might need several classes in order to provide the correct answer. 

Instructions:
Use only the node types and properties provided in the ontology.
Do not use any node types and properties that are not explicitly provided.
Include all necessary prefixes and relations.

The ontology is:
{ontology}

Note: Be as concise as possible.
Do not include any explanations or apologies in your responses.
Do not respond to any questions that ask for anything else than for you to construct a SPARQL query.
Do not include any text except for the SPARQL query generated.

The question is:
{question}
"""

SPARQL_LLM_PROMPT = """
Task: Generate a SPARQL SELECT statement for querying a graph database.
--- Examples ---
{examples}
Keep in mind that you might need several classes in order to provide the correct answer. 

Instructions:
Use only the node types and properties provided in the ontology.
Do not use any node types and properties that are not explicitly provided.
Include all necessary prefixes and relations.

The ontology is:
{ontology}

Note: Be as concise as possible.
Do not include any explanations or apologies in your responses.
Do not respond to any questions that ask for anything else than for you to construct a SPARQL query.
Do not include any text except for the SPARQL query generated.

The question is:
{question}
"""
FILL_TEMPLATES_PROMPT = """
Task: Generate a SPARQL SELECT statement for querying a graph database.

Instructions:
The SPARQL SELECT statement should answer the user question by filling in the provided query templates.
Use the ontology terminology to ensure the query is executable on the graph database.
Use the question mentioned ontology classes to guide the selection of the appropriate query template.

--- Ontology ---
{ontology}

--- Templates ---
{query_templates}

--- Examples ---
{examples}

--- Notes ---
Be as concise as possible.
Do not include any explanations or apologies in your responses.
Do not include any text except for the SPARQL query generated.

--- User Question ---
The user question is:
{question}

The answered SPARQL query is:
"""

PROMPT = """
Task: Generate a SPARQL SELECT statement for querying a graph database.
For instance, to find all email addresses of John Doe, the following query in backticks would be suitable:
```
PREFIX foaf: <http://xmlns.com/foaf/0.1/>
SELECT ?email
WHERE {{
    ?person foaf:name "John Doe" .
    ?person foaf:mbox ?email .
}}
```
Keep in mind that you might need several classes in order to provide the correct answer. 

Instructions:
Use only the node types and properties provided in the ontology.
Do not use any node types and properties that are not explicitly provided.
Include all necessary prefixes and relations.

The ontology is:
{ontology}

Note: Be as concise as possible.
Do not include any explanations or apologies in your responses.
Do not respond to any questions that ask for anything else than for you to construct a SPARQL query.
Do not include any text except for the SPARQL query generated.

The question is:
{question}

"""

PROMPT_additional_context = """
Task: Generate a SPARQL SELECT statement for querying a graph database.
For instance, to find all email addresses of John Doe, the following query in backticks would be suitable:
```
PREFIX foaf: <http://xmlns.com/foaf/0.1/>
SELECT ?email
WHERE {{
    ?person foaf:name "John Doe" .
    ?person foaf:mbox ?email .
}}
```
Keep in mind that you might need several classes in order to provide the correct answer. 

Instructions:
Use only the node types and properties provided in the ontology.
Do not use any node types and properties that are not explicitly provided.
Include all necessary prefixes and relations.

The ontology is:
{ontology}

Note: Be as concise as possible.
Do not include any explanations or apologies in your responses.
Do not respond to any questions that ask for anything else than for you to construct a SPARQL query.
Do not include any text except for the SPARQL query generated.

The question is:
{question}

Here is some additional content you might want to consider:
{context}

"""

VALIDATION_PROMPT = """
Task: Fix a SPARQL SELECT statement for querying a graph database that returned an error.
This query is supposed to answer some question, but it caused an error when executed.
Instructions:
Fix ONLY the error that is provided. Do not significantly change the structure of the query, but fix it to be valid.
The query should still answer the original question.

The ontology is:
{ontology}

Note: Be as concise as possible.
Do not include any explanations or apologies in your responses.
Do not respond to any questions that ask for anything else than for you to construct a SPARQL query.
Do not include any text except for the SPARQL query generated.

Here is the SPARQL query that caused an error:
{query}

Here is the error message:
{error}
"""
import re
import time


"""SimpleLLMQueryGenerator is a class that generates SPARQL queries from natural language questions using a language model (LLM).

Raises:
    FileNotFoundError: If the vocabulary file is not found.
    ValueError: If the vocabulary file is empty or invalid.
    ValueError: If the input data is invalid.
    RuntimeError: If the LLM model fails to generate a query.
    RuntimeError: If the query extraction fails.

Returns:
    _type_: _description_
"""


class SimpleLLMQueryGenerator(pipeline_stages.QueryGenerator):
    def __init__(self, model_name: str, verbose=False):
        super().__init__()
        self.verbose = verbose
        self.tries = 0
        self.max_tries = 3
        self.model_name = model_name
        if self.model_name == "gpt-4o-mini":
            self.llm_model_pipeline = gpt_pipeline(model_string=self.model_name)
        else:
            self.llm_model_pipeline = llm_pipeline.ModelPipeline(self.model_name)
        self.vocabulary = ""

        self.system_prompt = (
            "You are a system that returns only raw SPARQL queries. "
            "Do NOT include explanations, JSON, or any other formatting. "
            "Return only the SPARQL query, optionally inside triple backticks."
        )

    def initialize(self, data=None, **kwargs):
        """Initialize the SimpleLLMQueryGenerator.

        Args:
            data (_type_, optional): Data to initialize the generator. Defaults to None.

        Raises:
            FileNotFoundError: If the vocabulary file is not found.
        """
        vocab_path = kwargs.get("vocabulary_path")
        if not vocab_path:
            return
        elif not os.path.exists(vocab_path):
            raise FileNotFoundError(f"Vocabulary file not found: {vocab_path}")
        with open(vocab_path, "r") as file:
            self.vocabulary = file.read()

    def extract_sparql(self, response: str) -> str:
        """Extracts the SPARQL query from the LLM response.

        Args:
            response (str): The LLM response containing the SPARQL query.

        Raises:
            ValueError: If no valid SPARQL query is found in the response.

        Returns:
            str: The extracted SPARQL query.
        """
        # Prefer content inside markdown blocks if present
        markdown_match = re.search(r"```(?:sparql)?(.*?)```", response, re.DOTALL)
        if markdown_match:
            return markdown_match.group(1).strip()

        # If no backticks, fall back to raw text that looks like SPARQL
        if "SELECT" in response.upper() and "WHERE" in response.upper():
            return response.strip()

        raise ValueError("No valid SPARQL query found in response.")

    def run(self, data=None, **kwargs):
        """
        Runs the query generation process.

        Args:
            data (dict, optional): Input data for query generation. Defaults to None.
            **kwargs: Additional keyword arguments.

        Raises:
            ValueError: If the natural language question is missing.
        """
        natural_language_question = kwargs.get("natural_language_question")
        if not natural_language_question:
            raise ValueError("Missing 'natural_language_question' argument.")
        with open(
            "/home/mathiasyap/Code/university/phkg/MAI_Project_PHKG/src/data/new_ontology.ttl",
            "r",
        ) as f:
            ontology_serialized = f.read()

        prompt = FILL_TEMPLATES_PROMPT.format(
            ontology=ontology_serialized,
            query_templates=data["prompt_templates"],
            examples=data["prompt_examples"],
            question=data["natural_language_question"],
        )
        while self.tries < self.max_tries:
            if self.verbose:
                print(f"\n🧠 Attempt {self.tries}: Prompting LLM...\n")
            raw_output = self.llm_model_pipeline.generate(prompt, self.system_prompt)
            try:
                query = self.extract_sparql(raw_output)
                if self.verbose:
                    print("\n✅ Final SPARQL Query:\n", query)
                data["query"] = query
                data["attempts"] = self.tries
                return data
            except Exception as e:
                if self.verbose:
                    print(f"\n Parsing failed on attempt {self.tries}: {e}")
                time.sleep(1)

        raise RuntimeError("❌ All attempts to extract a valid SPARQL query failed.")

    def handle_query_error(self, data, error: str, **kwargs):
        """
        Handles errors that occur during query execution.
        This method attempts to fix the SPARQL query based on the error message.
        Args:
            data (dict): The data containing the original query and other information.
            error (str): The error message returned from the SPARQL query execution.
            **kwargs: Additional keyword arguments.
        """

        error_message = f"This SPARQL query returned an error: {error}. Fix this error in the query and try again. Again, do not include any explanations or apologies in your responses."
        self.tries += 1
        prompt = VALIDATION_PROMPT.format(
            ontology=self.vocabulary, query=data["query"], error=error_message
        )
        raw_output = self.llm_model_pipeline.generate(prompt, self.system_prompt)
        try:
            fixed_query = self.extract_sparql(raw_output)
            if self.verbose:
                print("Query fixing prompt: " + error_message)
                print("\n✅ Fixed SPARQL Query:\n", fixed_query)
            data["query"] = fixed_query
            data["attempts"] = self.tries
            return data
        except Exception as e:
            if self.verbose:
                print(f"\n⚠️ Failed to extract fixed query: {e}")
            if self.tries >= self.max_tries:
                self.tries = 0
                raise RuntimeError("All attempts to fix the SPARQL query failed.")

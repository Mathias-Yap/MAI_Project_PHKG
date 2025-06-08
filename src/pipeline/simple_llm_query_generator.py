import os
from rdflib import Graph
from . import pipeline_stages
from .llm import llm_pipeline

from utils.graph import load_graph
import json

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

class SimpleLLMQueryGenerator(pipeline_stages.QueryGenerator):
    def __init__(self, model_name: str):
        super().__init__()
        self.tries = 0
        self.max_tries = 3
        self.model_name = model_name
        self.llm_model_pipeline = llm_pipeline.ModelPipeline(self.model_name)
        self.vocabulary = ""

    def initialize(self, data=None, **kwargs):
        vocab_path = kwargs.get("vocabulary_path")
        if not vocab_path:
            return
        elif not os.path.exists(vocab_path):
            raise FileNotFoundError(f"Vocabulary file not found: {vocab_path}")
        with open(vocab_path, 'r') as file:
            self.vocabulary = file.read()

    def extract_sparql(self, response: str) -> str:
        # Prefer content inside markdown blocks if present
        markdown_match = re.search(r"```(?:sparql)?(.*?)```", response, re.DOTALL)
        if markdown_match:
            return markdown_match.group(1).strip()

        # If no backticks, fall back to raw text that looks like SPARQL
        if "SELECT" in response.upper() and "WHERE" in response.upper():
            return response.strip()

        raise ValueError("No valid SPARQL query found in response.")
    

    def run(self, data=None, **kwargs):
        natural_language_question = kwargs.get("natural_language_question")
        if not natural_language_question:
            raise ValueError("Missing 'natural_language_question' argument.")

        context = kwargs.get("context")
        ontology_serialized = load_graph("ontology").serialize(format="turtle")

        system_prompt = (
            "You are a system that returns only raw SPARQL queries. "
            "Do NOT include explanations, JSON, or any other formatting. "
            "Return only the SPARQL query, optionally inside triple backticks."
        )

        prompt = PROMPT_additional_context.format(
            ontology=ontology_serialized,
            question=natural_language_question,
            context=context or ""
        )
        print(f"Prompt: {prompt}")

        while( self.tries < self.max_tries):
            print(f"\n🧠 Attempt {self.tries}: Prompting LLM...\n")
            raw_output = self.llm_model_pipeline.generate(prompt, system_prompt)
            print("📥 Raw LLM Output:\n", raw_output)
            try:
                query = self.extract_sparql(raw_output)
                print("\n✅ Final SPARQL Query:\n", query)
                return {"query": query}
            except Exception as e:
                print(f"\n Parsing failed on attempt {self.tries}: {e}")
                time.sleep(1)

        raise RuntimeError("❌ All attempts to extract a valid SPARQL query failed.")


    def handle_query_error(self, query:str, error: str, **kwargs):
        error_message = f"This SPARQL query returned an error: {error}. Fix the query and try again. Again, do not include any explanations or apologies in your responses." 
        self.tries += 1
        system_prompt = (
            "You are a system that returns only raw SPARQL queries. "
            "Do NOT include explanations, JSON, or any other formatting. "
            "Return only the SPARQL query, optionally inside triple backticks."
        )
        prompt = (
            VALIDATION_PROMPT.format(
            ontology=self.vocabulary,
            query=query,
            error=error_message
            )
        )
        raw_output = self.llm_model_pipeline.generate(prompt, system_prompt)
        try:
            print("Query fixing prompt: " + error_message)
            fixed_query = self.extract_sparql(raw_output)
            print("\n✅ Fixed SPARQL Query:\n", fixed_query)
            return {"query": fixed_query}
        except Exception as e:
            print(f"\n⚠️ Failed to extract fixed query: {e}")
            if self.tries >= self.max_tries:
                self.tries = 0
                raise RuntimeError("All attempts to fix the SPARQL query failed.")


def main():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    data_path = os.path.join(base_dir, "data", "rdf_400_sphn.nt")
    vocab_path = os.path.join("../results", "vocabulary_rdf_400_sphn.txt")

    print(f"📂 Loading RDF data from: {data_path}")
    g = Graph()
    g.parse(data_path, format="nt")

    generator = SimpleLLMQueryGenerator("meta-llama/Llama-3.2-1B-Instruct")
    generator.initialize(vocabulary_path=vocab_path)

    question = "Which patients have had a lab test result with the code d_labitems/50911?"
    sparql_query = generator.run(natural_language_question=question)

    try:
        print("\n🔍 Query Results:")
        results = g.query(sparql_query)
        for row in results:
            print(row)
    except Exception as e:
        print(f"\n❌ Failed to execute query:\n{e}")


if __name__ == '__main__':
    main()

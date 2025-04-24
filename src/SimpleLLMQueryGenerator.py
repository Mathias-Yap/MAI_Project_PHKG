import os
import re
from rdflib import Graph
import PipelineStages
import LLM_Pipeline


class SimpleLLMQueryGenerator(PipelineStages.QueryGenerator):
    def __init__(self, model_name: str):
        super().__init__()
        self.model_name = model_name
        self.llm_model_pipeline = LLM_Pipeline.ModelPipeline(self.model_name)
        self.vocabulary = ""

    def initialize(self, data=None, **kwargs):
        vocab_path = kwargs.get("vocabulary_path")
        if not vocab_path or not os.path.exists(vocab_path):
            raise FileNotFoundError(f"Vocabulary file not found: {vocab_path}")
        with open(vocab_path, 'r') as file:
            self.vocabulary = file.read()

    def extract_sparql(self, response: str) -> str:
        match = re.search(r"```sparql(.*?)```", response, re.DOTALL | re.IGNORECASE)
        if match:
            return match.group(1).strip()
        match = re.search(r"(PREFIX\s+[^\n]+\n)*(SELECT|ASK|CONSTRUCT|DESCRIBE)\b.*", response,
                          re.DOTALL | re.IGNORECASE)
        if match:
            return match.group(0).strip()
        return response.strip()

    def clean_query_format(self, query: str) -> str:
        """Fix spacing and common SPARQL syntax issues."""
        query = re.sub(r"\b(SELECT|ASK|CONSTRUCT|DESCRIBE)\s*(?=\?)", r"\1 ", query, flags=re.IGNORECASE)
        query = re.sub(r"(\w+:\w+)(\?)", r"\1 \2", query)
        query = re.sub(r"(\?\w+)([.;])", r"\1 \2", query)
        return query.strip()

    def run(self, data=None, **kwargs):
        natural_language_question = kwargs.get("natural_language_question")
        if not natural_language_question:
            raise ValueError("Missing 'natural_language_question' argument.")

        system_prompt = (
            "You are a system that ONLY returns clean, working SPARQL queries. "
            "Do NOT explain. Do NOT use markdown. Do NOT prefix with 'SPARQL:' or '```'."
        )

        prompt = (
            "You are given a knowledge graph that uses the SPHN ontology with the following vocabulary:\n"
            f"{self.vocabulary}\n\n"
            "Here is an example of a correct SPARQL query:\n"
            "Question: Which patients have had a lab test result with the code d_labitems/51491?\n"
            "SPARQL:\n"
            "PREFIX sphn: <https://www.biomedit.ch/rdf/sphn-schema/sphn/>\n"
            "SELECT ?patient\n"
            "WHERE {\n"
            "  ?event a sphn:LabTestEvent ;\n"
            "         sphn:hasSubjectPseudoIdentifier ?patient ;\n"
            "         sphn:hasLabTest ?result .\n"
            "  ?result a sphn:LabResult ;\n"
            "          sphn:hasCode <https://www.biomedit.ch/rdf/sphn-schema/sphn/d_labitems/51491> .\n"
            "}\n\n"
            "Now answer the following question in SPARQL only — no explanation, no markdown, no labels.\n"
            f"Question: {natural_language_question}\n"
            "SPARQL:\n"
        )

        print(f"\n🧠 Prompting LLM:\n{prompt}\n")
        raw_output = self.llm_model_pipeline.generate(prompt, system_prompt)
        print("📥 Raw LLM Output:\n", raw_output)

        query = self.extract_sparql(raw_output)
        query = self.clean_query_format(query)

        print("\n✅ Final SPARQL Query:\n", query)
        return {"query": query}


def main():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    data_path = os.path.join(base_dir, "data", "rdf_400_sphn.txt")
    vocab_path = os.path.join("results", "vocabulary_rdf_400_sphn.txt")

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

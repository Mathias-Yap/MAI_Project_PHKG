import millenniumdb_driver
from .simple_llm_query_generator import SimpleLLMQueryGenerator 
from .pipeline_stages import PipelineStep
from .query_engine_component import QueryExecutorStep

class MDBValidatedGeneration(SimpleLLMQueryGenerator):
    def __init__(self, model_name: str):
        super().__init__(model_name)
        self.query_executor = QueryExecutorStep(engine_name = "milleniumDB", graph_path="rdf_100_sphn.nt",construct_graph=False)
        
        self.llm_generator = SimpleLLMQueryGenerator(model_name)

    def run(self, data=None, **kwargs):
        """
        Runs the MDB validated generation pipeline.
        
        :param data: Input data required for query generation.
        :param kwargs: Additional arguments.
        :return: Generated SPARQL query or error message.
        """
        # Get the initial query from the LLM generator
        query = self.llm_generator.run(data, **kwargs)

        # Loop until a valid query is generated or max tries are reached
        while(self.llm_generator.tries <= self.llm_generator.max_tries):
            try:
                print(f"\n🧠 Attempt {self.llm_generator.tries}: Executing query...\n{query['query']}\n")
                # Execute the query using the query executor
                result = self.query_executor.run(data = query, **kwargs)
                return result
            except Exception as e:
                
                # print(f"Exception type: {type(e)}")
                # print(f"Exception dir: {dir(e)}")  # Shows all available attributes
                # print(f"Exception vars: {vars(e)}")  # Shows instance variables
                # Handle query error and attempt to fix it
                if self.llm_generator.tries >= self.llm_generator.max_tries:
                    print("❌ Maximum attempts reached. Unable to generate a valid query.")
                    raise RuntimeError("All attempts to fix the SPARQL query failed.")
                print("Query execution failed:", e.args[0], "\nAttempting to fix the query...")
                query = self.llm_generator.handle_query_error(query, str(e), **kwargs)

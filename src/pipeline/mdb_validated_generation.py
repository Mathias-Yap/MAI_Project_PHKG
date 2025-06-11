import time
import traceback
import millenniumdb_driver
from .simple_llm_query_generator import SimpleLLMQueryGenerator 
from .pipeline_stages import PipelineStep
from .query_engine_component import QueryExecutorStep

class MDBValidatedGeneration(PipelineStep):
    def initialize(self, data, **kwargs):
        return super().initialize(data, **kwargs)
    
    def __init__(self, model_name: str):
        self.query_executor = QueryExecutorStep(engine_name = "milleniumDB", graph_path="rdf_400_sphn_augmented_hybrid.ttl",construct_graph=False)
        self.llm_generator = SimpleLLMQueryGenerator(model_name)

    def run(self, data=None, **kwargs):
        """
        Runs the MDB validated generation pipeline.
        
        :param data: Input data required for query generation.
        :param kwargs: Additional arguments.
        :return: Generated SPARQL query or error message.
        """
        data["validation_time"] = []
        data["valid_query"] = False
        self.llm_generator.tries = 0
        # Get the initial query from the LLM generator
        start_init_query_time = time.time()
        data = self.llm_generator.run(data, **kwargs)
        data["initial_query_time"] = time.time() - start_init_query_time 
        # Loop until a valid query is generated or max tries are reached
        while(self.llm_generator.tries <= self.llm_generator.max_tries):
            try:
                # print(f"\n🧠 Attempt {self.llm_generator.tries}: Executing query...\n{data["query"]}\n")
                # Execute the query using the query executor
                data = self.query_executor.run(data, **kwargs)
                data["valid_query"] = True
                return data
            except millenniumdb_driver.MillenniumDBError:
                start_validation_time = time.time()
                full_traceback =  traceback.format_exc()
                error_message = ""
                for line in full_traceback.splitlines():
                    if "Query Exception:" in line:
                        error_message = line.split("Query Exception:")[1]
                if self.llm_generator.tries >= self.llm_generator.max_tries:
                    print("❌ Maximum attempts reached. Unable to generate a valid query.")
                    print("Failed query: " + data["query"])
                    print("Error message: " + error_message)
                    return data
                data = self.llm_generator.handle_query_error(data, error_message, **kwargs)
                data["validation_time"].append(time.time() - start_validation_time)

    
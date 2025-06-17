from .pipeline_stages import PipelineStep
from .simple_llm_query_generator import SimpleLLMQueryGenerator
from .query_engine_component import QueryExecutorStep
import time

"""Pipeline class for managing a sequence of processing steps.
This class allows for the initialization, execution, and closing of a series of steps in a pipeline.
"""


class Pipeline:
    def __init__(self, steps: list[PipelineStep], verbose=False):
        self.verbose = verbose
        self.steps = steps

    def initialize(self, initial_data=None, **kwargs):
        """Initialize the pipeline with the given initial data.
        This method calls the initialize method of each step in the pipeline."""
        data = initial_data
        for step in self.steps:
            step.initialize(data, **kwargs)

    def run(self, initial_data=None, **kwargs):
        """Run the pipeline with the given initial data.
        This method executes each step in the pipeline sequentially.
        Args:
            initial_data (dict): The initial data to be processed by the pipeline.
            **kwargs: Additional keyword arguments to be passed to each step's run method.
        Returns:
            dict: The final data after processing through all steps.
        """
        total_start_time = time.time()
        data = initial_data
        for step in self.steps:
            step_name = step.__class__.__name__
            if self.verbose:
                print(f"▶ Running step: {step_name}")
            start_time = time.time()
            data = step.run(data, **kwargs)
            end_time = time.time()
            duration = end_time - start_time
            if self.verbose:
                print(f"✅ Step '{step_name}' completed in {duration:.2f} seconds\n")
        total_end_time = time.time()
        data["total_time"] = total_end_time - total_start_time
        return data

    def close(self):
        """Close the pipeline and release any resources."""
        for step in self.steps:
            step.close()


class InitialPipeline(Pipeline):
    def __init__(self, steps: list[PipelineStep], verbose=False):
        super().__init__(steps)


if __name__ == "__main__":
    import os
    import traceback

    pipe = InitialPipeline([])
    try:
        query_generator = SimpleLLMQueryGenerator(
            model_name="meta-llama/Llama-3.2-1B-Instruct"
        )
        question = (
            "Which patients have had a lab test result with the code d_labitems/50911?"
        )
        query_executor = QueryExecutorStep(
            engine_name="milleniumDB",
            graph_path="rdf_100_sphn.nt",
            verbose=True,
            query_format="sparql",
            construct_graph=False,
        )

        answer_generator = RetrievalAugmentedAnswerLLM(
            model_name="meta-llama/Llama-3.2-1B-Instruct"
        )

        pipe.steps.append(query_generator)
        pipe.steps.append(query_executor)
        pipe.steps.append(answer_generator)

        pipe.initialize()
        result = pipe.run(natural_language_question=question, sparql_is_path=False)
        print(
            f"The Pipeline generated the following output:\n"
            f"The generated query: {result['query']}\n"
            f"The query result: {result['result'].values()}\n"
            f"The generated answer: {result['answer']}"
        )

    except Exception as ex:
        traceback.print_exc()

    finally:
        pipe.close()

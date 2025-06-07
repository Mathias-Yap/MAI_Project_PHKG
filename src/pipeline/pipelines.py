from .pipeline_stages import PipelineStep
from .rag_answer_llm import RetrievalAugmentedAnswerLLM
from .simple_llm_query_generator import SimpleLLMQueryGenerator
from .query_engine_component import QueryExecutorStep


import time

class Pipeline:
    def __init__(self, steps: list[PipelineStep]):
        self.steps = steps

    def initialize(self, initial_data=None, **kwargs):
        data = initial_data
        for step in self.steps:
            step.initialize(data, **kwargs)

    def run(self, initial_data=None, **kwargs):
        data = initial_data
        for step in self.steps:
            step_name = step.__class__.__name__
            print(f"▶ Running step: {step_name}")
            start_time = time.time()
            data = step.run(data, **kwargs)
            end_time = time.time()
            duration = end_time - start_time
            print(f"✅ Step '{step_name}' completed in {duration:.2f} seconds\n")
        return data

    def close(self):
        for step in self.steps:
            step.close()


class InitialPipeline(Pipeline):
    def __init__(self, steps: list[PipelineStep]):
        super().__init__(steps)

if __name__ == '__main__':
    import os
    import traceback

    pipe = InitialPipeline([])
    try:
        query_generator = SimpleLLMQueryGenerator(model_name="meta-llama/Llama-3.2-1B-Instruct")
        question = "Which patients have had a lab test result with the code d_labitems/50911?"
        query_executor = QueryExecutorStep(engine_name="milleniumDB", graph_path="rdf_100_sphn.nt",
                                           verbose=True, query_format="sparql", construct_graph=False)

        answer_generator=RetrievalAugmentedAnswerLLM(model_name="meta-llama/Llama-3.2-1B-Instruct")


        pipe.steps.append(query_generator)
        pipe.steps.append(query_executor)
        pipe.steps.append(answer_generator)

        pipe.initialize()
        result = pipe.run(natural_language_question=question,sparql_is_path=False)
        print(f"The Pipeline generated the following output:\n"
              f"The generated query: {result['query']}\n"
              f"The query result: {result['result'].values()}\n"
              f"The generated answer: {result['answer']}")

    except Exception as ex:
        traceback.print_exc()

    finally:
        pipe.close()


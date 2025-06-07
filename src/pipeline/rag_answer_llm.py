from .pipeline_stages import PipelineStep
from .llm import llm_pipeline

class RetrievalAugmentedAnswerLLM(PipelineStep):
    def __init__(self, model_name="", **kwargs):
        super().__init__()
        self.model_name = model_name
        self.llm_model_pipeline = llm_pipeline.ModelPipeline(self.model_name)
        self.vocabulary = ""
    def initialize(self, data, **kwargs):
        pass

    def run(self, data=None, **kwargs):
        natural_language_question=kwargs["natural_language_question"]
        if natural_language_question is None:
            print("There is no Natural Language Question!")

        query = data["query"]
        if query is None:
            print("There is no query!")

        result=data["result"]
        if result is None:
            print("There is no result!")


        prompt=f"""
        
        I have a natural language question: 
        
        "{natural_language_question}".
        
        I queried the following on a Personal Health Knowledge Graph: 
        
        "{query}".
        
        This is the result of the query: "{result.values()}".
        
        Can you answer the natural language question using the retrieved information from the Personal Health Knowledge Graph in a human readable way? Do not include anything but the answer to that question in your answer.
        
        """

        print(f"Prompting the Answer Generator with the following: {prompt}")

        raw_llm_output=self.llm_model_pipeline.generate(prompt)

        data["answer"]=raw_llm_output

        return data


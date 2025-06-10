from .nlq_vector_store import QuestionTemplateVectorStore
from .vector_store import VectorStore
from pipeline.pipeline_stages import PipelineStep
class context_constructor(PipelineStep):

    def __init__(self,construct_vector_store: bool = False, example_queries_file:str|None = None):
        """_summary_

        Args:
            ontology_file (str | None, optional): _description_. Defaults to None.
            example_queries_file (str | None, optional): _description_. Defaults to None.
        """
        if(construct_vector_store):
            self.class_vector_store = VectorStore()
        else:
            self.class_vector_store = VectorStore(file_name="classes")
        if example_queries_file is not None:
            self.nlq_store = QuestionTemplateVectorStore(yaml_file=example_queries_file)
        else:
            self.nlq_store = QuestionTemplateVectorStore(file_name="questions")

    def initialize(self, data, **kwargs):
        return super().initialize(data, **kwargs)

    def verify_template_classes(self, classes, template):
        pass
        
    def get_template_fill_context(self,question:str):
        classes, properties = self.class_vector_store.query(
        question
        )
        classes = classes + properties
        qq_examples = self.nlq_store.query(
            question
        )
        most_similar_template = qq_examples[0] if qq_examples else ""
        templates = ""
        examples = ""
        for i, example in enumerate(qq_examples):
            print("example {i}" , example)
            template = "\n".join([
                f"Template {i}:",
                f"Template Question: {example['question_template']}",
                f"Template Query: {example['query_template']}"
            ])
            example_string = "\n".join([
                f"Example {i}:",
                f"Question: {example['question_example']}",
                # f"Relevant Classes: TODO add {classes}",
                f"Answer Example {i}: {example['query_example']}"
            ])
            examples += example_string + "\n\n"
            templates += template + "\n\n"
        
        print("examples in get_template:", examples)
        return templates, examples, classes
    def get_context(self, question: str):
        qq_examples = self.nlq_store.query(
            question
        )
        classes = self.class_vector_store.query(
            question
        )
        formatted_examples = "\n".join([
        f"Question: {example['question_template']}\nQuery: {example['query_template']}\n"
        for example in qq_examples
        ])
        formatted_classes = "\n".join([f"Class IRI: {cls}" for cls in classes])
        self.context = (
            "Next follow template questions and queries related to the natural language question:\n"
            f"{formatted_examples}\n"
            "The following class IRIs can be placed in place of the classes enclosed by brackets \{\} in the templates:\n"
            f"{formatted_classes}\n"
        )
        return self.context

    def run(self,data,**kwargs):
        data["prompt_templates"], data["prompt_examples"], data["relevant_classes"] = self.get_template_fill_context(data["natural_language_question"])
        return data

if __name__ == "__main__":
    constructor = context_constructor()
    context = constructor.get_context("How many substances does drug 12305 contain?")
    print(context)

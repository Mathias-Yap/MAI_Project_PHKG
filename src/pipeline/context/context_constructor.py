from .nlq_vector_store import QuestionTemplateVectorStore
from .vector_store import VectorStore
class context_constructor:
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
if __name__ == "__main__":
    constructor = context_constructor()
    context = constructor.get_context("How many substances does drug 12305 contain?")
    print(context)

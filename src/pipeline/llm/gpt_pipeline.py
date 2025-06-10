from langchain_core.messages import HumanMessage, SystemMessage
from langchain_community.callbacks import get_openai_callback
from langchain_openai import ChatOpenAI
class gpt_pipeline:
    def __init__(self, model_string: str, max_length: int = 500, temperature: float = 0.3):
        openai_key = ""
        self.model = ChatOpenAI(model="gpt-4o-mini", api_key=openai_key)
        self.cost = 0
        self.requests = 0

    def generate(self, prompt, system_prompt):
        """
        Ask the language model a question.
        :param message: The message to ask the language model.
        :return: The result of the language model.
        """
        # Retrieve the result from the language model
        system_message = SystemMessage(content = system_prompt) 
        message = HumanMessage(content=prompt)

        with get_openai_callback() as cb:
            result = self.model.invoke([system_message, message]).content
            self.cost += cb.total_cost
            self.requests += 1
            print(
            f"Cost (USD): ${format(cb.total_cost, '.6f')}"
            ) 
        
        # Extract the result in case the start phrase is provided
        start_phrase = "The result is:"
        start_pos = result.find(start_phrase)
        if start_pos != -1:
            result = result[start_pos + len(start_phrase) :].strip()

        return result
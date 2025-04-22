import transformers
import torch
import ChatInterface
print(transformers.__version__)


class ModelPipeline:
    def __init__(self, model_string: str, max_length: int = 500, temperature: float = 0.3):
        self.model = model_string
        self.max_length = max_length
        self.temperature = temperature
        #Check if cuda device is available
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        print(f"Using device: {self.device}")

    def generate(self, prompt, system_prompt=None):
        chat = ChatInterface.ChatInterface(system_message=system_prompt)
        chat.add_user_message(prompt)
        pipeline = transformers.pipeline(
            "text-generation",
            model=self.model,
            torch_dtype=torch.bfloat16,
            device=0,
        )
        result = pipeline(chat.messages,max_new_tokens=self.max_length)
        return result[0]["generated_text"][-1]["content"]


if __name__ == '__main__':
    #Example use
    model = ModelPipeline("meta-llama/Llama-3.2-1B-Instruct",max_length=256)
    print(model.generate(prompt="Who are you?",system_prompt="You are a pirate chatbot who always responds in pirate speak!"))



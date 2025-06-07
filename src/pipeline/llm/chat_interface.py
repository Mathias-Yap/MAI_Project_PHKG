class ChatInterface:
    def __init__(self, system_message="You are a helpful assistant."):
        self.messages = [{"role": "system", "content": system_message}]

    def add_user_message(self, content):
        self.messages.append({"role": "user", "content": content})

    def add_assistant_message(self, content):
        self.messages.append({"role": "assistant", "content": content})

    def get_messages(self):
        return self.messages

    def reset_conversation(self, system_message="You are a helpful assistant."):
        self.messages = [{"role": "system", "content": system_message}]

    def to_string(self):
        return self.messages
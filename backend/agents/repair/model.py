from agents.base_model import GroqChatModel


class RepairModel(GroqChatModel):
    def __init__(self):
        super().__init__(max_tokens=8192)

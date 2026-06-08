from agents.base_model import GroqChatModel


class DocumentationModel(GroqChatModel):
    def __init__(self):
        super().__init__(temperature=0.2)

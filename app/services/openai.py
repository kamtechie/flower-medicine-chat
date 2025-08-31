from openai import OpenAI
from app.core.settings import settings


class OpenAIService:
    def __init__(self, api_key: str = ""):
        self.api_key = api_key or settings.OPENAI_API_KEY
        self.client = OpenAI(api_key=self.api_key)

    def embed(self, texts, model=None):
        model = model or settings.OPENAI_EMBED_MODEL
        response = self.client.embeddings.create(model=model, input=texts)
        return [d.embedding for d in response.data]

    def chat(self, messages, model=None, **kwargs):
        model = model or settings.OPENAI_CHAT_MODEL
        response = self.client.chat.completions.create(
            model=model, messages=messages, **kwargs
        )
        return response.choices[0].message.content

    def response(
        self, input, model=None, schema=None, **kwargs
    ):
        model = model or settings.OPENAI_CHAT_MODEL
        response = None
        if schema:
            response = self.client.responses.parse(
                model=model, input=input, text_format=schema, **kwargs
            )
        else:
            response = self.client.responses.create(
                model=model, input=input, **kwargs
            )
        return response.output_text

    # Add more OpenAI API wrappers as needed

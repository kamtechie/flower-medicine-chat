from app.prompts.recommender import RECOMMENDER_SYSTEM
from app.core.settings import settings
from app.services.openai import OpenAIService
from app.services.retriever import Retriever

class Recommender:
    def __init__(self, oa: OpenAIService, model: str, retriever: Retriever):
        self.openai = oa
        self.model = model
        self.retriever = retriever

    def recommend(self, summary: str, k: int = 12) -> str:
        ctx = self.retriever.retrieve(summary, k=min(settings.TOP_K*2, k))
        ctx_text = "\n\n".join([
            f"{c['text']}\n(Source: {c['meta'].get('source','')}{', p.'+str(c['meta'].get('page')) if c['meta'].get('page') else ''})"
            for c in ctx
        ])
        prompt = f"User summary: {summary}\n\nContext passages:\n{ctx_text}\n\nNow produce recommendations as per the system format."
        response = self.openai.response(
            model=self.model,
            input=[{"role":"system","content":RECOMMENDER_SYSTEM},{"role":"user","content":prompt}],
        )
        return response

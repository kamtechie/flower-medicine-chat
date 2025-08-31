from app.models.dialog_models import DialogAction, SessionState
from app.prompts.planner import PLANNER_SYSTEM, PLANNER_FEWSHOT
from pydantic import ValidationError

from app.services.openai import OpenAIService

class Planner:
    def __init__(self, oa: OpenAIService, model: str):
        self.openai = oa
        self.model = model

    def plan(self, state: SessionState, user_msg: str) -> DialogAction:
        msgs = [{"role":"system","content":PLANNER_SYSTEM}] + PLANNER_FEWSHOT + [
            {"role":"user","content":f"Session so far: {state.model_dump_json()}"},
            {"role":"user","content":user_msg},
        ]
        response = self.openai.response(
            model=self.model,
            schema=DialogAction,
            input=msgs,
        )
        try:
            return DialogAction.model_validate_json(response)
        except ValidationError as e:
            raise ValueError(f"Planner JSON parse failed: {e}")

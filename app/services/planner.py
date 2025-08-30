from app.models.dialog_models import DialogAction, SessionState
from app.prompts.planner import PLANNER_SYSTEM, PLANNER_FEWSHOT
from pydantic import ValidationError

class Planner:
    def __init__(self, oa, model: str):
        self.oa = oa
        self.model = model

    def plan(self, state: SessionState, user_msg: str) -> DialogAction:
        msgs = [{"role":"system","content":PLANNER_SYSTEM}] + PLANNER_FEWSHOT + [
            {"role":"user","content":f"Session so far: {state.model_dump_json()}"},
            {"role":"user","content":user_msg},
        ]
        resp = self.oa.responses.parse(
            model=self.model,
            text_format=DialogAction,
            input=msgs,
        )
        try:
            return DialogAction.model_validate_json(resp.output_text)
        except ValidationError as e:
            raise ValueError(f"Planner JSON parse failed: {e}")

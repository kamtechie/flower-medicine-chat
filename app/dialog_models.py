from typing import List, Optional, Literal
from pydantic import BaseModel, Field

Stage = Literal["ask_feelings", "ask_context", "ask_duration", "ask_goal","confirm", "recommend", "end"]
Duration = Literal["acute", "persistent"]
Safety = Literal["ok", "crisis", "medical"]


class SessionState(BaseModel):
    stage: Stage = "ask_feelings"
    feelings: List[str] = Field(default_factory=list)  # 1–6 short, lowercase tokens
    context: Optional[str] = None                      # <= 140 chars
    duration: Optional[Duration] = None
    goal: Optional[str] = None                         # <= 80 chars
    turns: List[dict] = Field(default_factory=list)    # [{"role": "user"|"assistant", "content": str}]


class DialogAction(BaseModel):
    # What the planner wants to do next
    stage: Stage
    next_question: Optional[str] = None                # ask at most one question per turn
    summary: Optional[str] = None                      # short running summary
    needed_slots: List[str] = Field(default_factory=list)  # subset of ["feelings","context","duration","goal"]
    safety: Safety = "ok"

    # Slots the planner can infer/update THIS turn
    feelings: Optional[List[str]] = None               # 1–6 items, lowercase
    context: Optional[str] = None                      # <= 140 chars
    duration: Optional[Duration] = None
    goal: Optional[str] = None                         # <= 80 chars

    # Only when stage == "recommend" (optional)
    recommendation_text: Optional[str] = None

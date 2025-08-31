from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel

from app.models.dialog_models import SessionState, DialogAction
from app.core.deps import get_planner, get_recommender, get_logger
from app.services.planner import Planner
from app.services.recommender import Recommender
from app.services.logger import LoggerService
from app.sessions.sessions_memory import MemoryStore

router = APIRouter()


session_store = MemoryStore()




class StartOut(BaseModel):
    session_id: str
    message: str

@router.post("/session", response_model=StartOut)
def create_session():
    sid = session_store.new()
    return StartOut(session_id=sid, message="Hi—how can I help today? In a few words, how do you feel.")

class ChatIn(BaseModel):
    session_id: str
    message: str

class ChatOut(BaseModel):
    reply: str
    stage: str


def _update_session_state(state: SessionState, action: DialogAction):
    """Update session from planner output (merge)"""
    state.stage = action.stage
    if action.feelings:
        merged = set(state.feelings)
        for w in action.feelings:
            w = (w or "").strip().lower()
            if w:
                merged.add(w)
        state.feelings = list(merged)[:6]
    if action.context:
        c = action.context.strip()
        state.context = (c[:140]) if c else state.context
    if action.duration in ("acute", "persistent"):
        state.duration = action.duration
    if action.goal:
        g = action.goal.strip()
        state.goal = (g[:80]) if g else state.goal



@router.post("/chat", response_model=ChatOut)
def chat_step(
    payload: ChatIn,
    planner: Planner = Depends(get_planner),
    recommender: Recommender = Depends(get_recommender),
    logger: LoggerService = Depends(get_logger),
):
    sid = payload.session_id
    state = session_store.get(sid)
    if not state:
        raise HTTPException(status_code=401, detail="invalid session_id")

    user_msg = payload.message.strip()
    state.turns.append({"role":"user","content":user_msg})

    try:
        action = planner.plan(state, user_msg)
    except Exception as e:
        logger.exception("Planner failed: %s", e)
        raise HTTPException(status_code=500, detail="Planner failed.")

    logger.info(f"Planner action: {action.model_dump()}")
    _update_session_state(state, action)
    session_store.set(sid, state)

    if action.safety in ("crisis","medical"):
        text = ("I'm concerned by what you shared. I can't provide recommendations in potential crisis situations. "
                "Please consider reaching out to a trusted person or local professional support. "
                "If you're in immediate danger, contact local emergency services.")
        state.turns.append({"role":"assistant","content":text})
        session_store.set(sid, state)
        return ChatOut(reply=text, stage="end")

    if action.stage in ("ask_feelings","ask_context","ask_duration"):
        question = action.next_question or "Could you tell me a bit more?"
        state.turns.append({"role":"assistant","content":question})
        session_store.set(sid, state)
        return ChatOut(reply=question, stage=action.stage)

    if action.stage == "confirm":
        question = action.next_question or (action.summary or "Shall I suggest a few essences?")
        state.turns.append({"role":"assistant","content":question})
        session_store.set(sid, state)
        return ChatOut(reply=question, stage="confirm")

    if action.stage in ("recommend","end"):
        summary = action.summary or "feelings and context as discussed"
        text = action.recommendation_text or recommender.recommend(summary)
        state.turns.append({"role":"assistant","content":text})
        session_store.set(sid, state)
        return ChatOut(reply=text, stage="recommend")

    question = action.next_question or "How are you feeling right now?"
    state.turns.append({"role":"assistant","content":question})
    session_store.set(sid, state)
    return ChatOut(reply=question, stage=action.stage)

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, List
import os, json, uuid

from app.prompts.planner import PLANNER_FEWSHOT, PLANNER_SYSTEM
from app.retrieval import _embed

from .dialog_models import SessionState, DialogAction
from .chroma import coll
from .config import OPENAI_CHAT_MODEL, TOP_K, logger
from openai import OpenAI
import time
from app.services.planner import Planner
from app.services.recommender import Recommender
from app.services.retriever import Retriever

router = APIRouter()

SESSIONS: dict[str, SessionState] = {}


oa = OpenAI()  # requires OPENAI_API_KEY
retriever = Retriever(coll)
planner = Planner(oa, OPENAI_CHAT_MODEL)
recommender = Recommender(oa, OPENAI_CHAT_MODEL, retriever)

class StartOut(BaseModel):
    session_id: str
    message: str

@router.post("/session", response_model=StartOut)
def create_session():
    sid = str(uuid.uuid4())
    SESSIONS[sid] = SessionState()
    return StartOut(session_id=sid, message="Hi—how can I help today? In a few words, how do you feel?")

class ChatIn(BaseModel):
    session_id: str
    message: str

class ChatOut(BaseModel):
    reply: str
    stage: str

def _update_session_state(state: SessionState, action: DialogAction):
        # Update session from planner output (merge)
    state.stage = action.stage

    # feelings: merge unique, keep 1..6 lowercase tokens
    if action.feelings:
        merged = set(state.feelings)
        for w in action.feelings:
            w = (w or "").strip().lower()
            if w:
                merged.add(w)
        state.feelings = list(merged)[:6]

    # context: take latest non-empty (truncate to 140)
    if action.context:
        c = action.context.strip()
        state.context = (c[:140]) if c else state.context

    # duration: only accept acute|persistent
    if action.duration in ("acute", "persistent"):
        state.duration = action.duration

    # goal: take latest non-empty (truncate to 80)
    if action.goal:
        g = action.goal.strip()
        state.goal = (g[:80]) if g else state.goal


def _plan_next(state: SessionState, user_msg: str) -> DialogAction:
    # Build compact turn history
    msgs = [{"role":"system","content":PLANNER_SYSTEM}] + PLANNER_FEWSHOT + [
        {"role":"user","content":f"Session so far: {state.model_dump_json()}"},
        {"role":"user","content":user_msg},
    ]
    start_time = time.time()
    resp = oa.responses.parse(
        model=OPENAI_CHAT_MODEL,
        text_format=DialogAction,
        input=msgs,
    )
    elapsed = time.time() - start_time
    logger.info(f"OpenAI planner request took {elapsed:.2f} seconds")
    try:
        return DialogAction.model_validate_json(resp.output_text)
    except Exception as e:
        logger.exception("Planner JSON parse failed: %s", e)
        raise HTTPException(status_code=500, detail="Planner failed to return valid JSON.")

def _retrieve_for(summary: str, k: int = 12) -> List[Dict[str, Any]]:
    qvecs = _embed([summary], oa)
    if not qvecs:
        raise HTTPException(status_code=400, detail="Failed to embed question.")
    qvec = qvecs[0]
    res = coll.query(query_embeddings=[qvec], n_results=k)
    docs = res.get("documents", [[]])[0]
    metas = res.get("metadatas", [[]])[0]
    return [{"text": d, "meta": m} for d, m in zip(docs, metas)]

RECOMMENDER_SYSTEM = """You are Zenji, a careful assistant recommending Bach/flower essences.
Use ONLY the provided context passages. Do not diagnose or make medical claims.
Map the user's feelings/context/duration to 3–6 essences. Keep it concise and kind.
Do not include citations.
Output format (plain text):
- Title line: Suggested essences
- Bulleted list: Essence — 1-sentence rationale
- Blend idea: a short line combining 2–5 essences
- Usage: brief, general usage guidance and a one-line disclaimer
"""

def _recommend_text(user_summary: str, ctx: List[Dict[str, Any]]) -> str:
    parts = []
    for c in ctx:
        m = c["meta"]; src = m.get("source",""); page = m.get("page")
        where = f"{src}" + (f", p.{page}" if page else "")
        # keep context minimal; no explicit citation markup
        parts.append(f"{c['text']}\n(Source: {where})")
    ctx_text = "\n\n".join(parts[:12])

    prompt = f"User summary: {user_summary}\n\nContext passages:\n{ctx_text}\n\nNow produce recommendations as per the system format."
    start_time = time.time()
    response = oa.responses.create(
        model=OPENAI_CHAT_MODEL,
        input=[{"role":"system","content":RECOMMENDER_SYSTEM},{"role":"user","content":prompt}],
    )
    elapsed = time.time() - start_time
    logger.info(f"OpenAI recommender request took {elapsed:.2f} seconds")
    return response.output_text

@router.post("/chat", response_model=ChatOut)
def chat_step(payload: ChatIn):
    sid = payload.session_id
    state = SESSIONS.get(sid)
    if not state:
        raise HTTPException(status_code=400, detail="invalid session_id")

    user_msg = payload.message.strip()
    state.turns.append({"role":"user","content":user_msg})

    try:
        action = planner.plan(state, user_msg)
    except Exception as e:
        logger.exception("Planner failed: %s", e)
        raise HTTPException(status_code=500, detail="Planner failed.")

    logger.info(f"Planner action: {action.model_dump()}")
    _update_session_state(state, action)

    if action.safety in ("crisis","medical"):
        text = ("I'm concerned by what you shared. I can't provide recommendations in potential crisis situations. "
                "Please consider reaching out to a trusted person or local professional support. "
                "If you're in immediate danger, contact local emergency services.")
        state.turns.append({"role":"assistant","content":text})
        return ChatOut(reply=text, stage="end")

    if action.stage in ("ask_feelings","ask_context","ask_duration"):
        question = action.next_question or "Could you tell me a bit more?"
        state.turns.append({"role":"assistant","content":question})
        return ChatOut(reply=question, stage=action.stage)

    if action.stage == "confirm":
        question = action.next_question or (action.summary or "Shall I suggest a few essences?")
        state.turns.append({"role":"assistant","content":question})
        return ChatOut(reply=question, stage="confirm")

    if action.stage in ("recommend","end"):
        summary = action.summary or "feelings and context as discussed"
        text = action.recommendation_text or recommender.recommend(summary)
        state.turns.append({"role":"assistant","content":text})
        return ChatOut(reply=text, stage="recommend")

    question = action.next_question or "How are you feeling right now?"
    state.turns.append({"role":"assistant","content":question})
    return ChatOut(reply=question, stage=action.stage)

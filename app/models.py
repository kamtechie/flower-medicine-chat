from typing import List, Dict, Any, Optional
from pydantic import BaseModel

class AskIn(BaseModel):
    question: str
    where: Optional[Dict[str, Any]] = None
    k: Optional[int] = None

class AskOut(BaseModel):
    answer: str
    citations: List[Dict[str, str]]

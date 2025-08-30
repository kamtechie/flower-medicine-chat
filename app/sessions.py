from typing import Optional
from app.dialog_models import SessionState

class SessionStore:
    def get(self, sid: str) -> Optional[SessionState]:
        raise NotImplementedError
    def set(self, sid: str, state: SessionState) -> None:
        raise NotImplementedError
    def new(self) -> str:
        raise NotImplementedError

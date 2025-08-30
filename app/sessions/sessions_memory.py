import uuid
from app.models.dialog_models import SessionState
from app.sessions.sessions import SessionStore

class MemoryStore(SessionStore):
    _db: dict[str, SessionState] = {}

    def get(self, sid: str) -> SessionState | None:
        return self._db.get(sid)

    def set(self, sid: str, state: SessionState) -> None:
        self._db[sid] = state

    def new(self) -> str:
        sid = str(uuid.uuid4())
        self._db[sid] = SessionState()
        return sid

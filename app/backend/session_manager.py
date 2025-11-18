import json
import uuid
from pathlib import Path
from datetime import datetime

class SessionManager:
    def __init__(self, sessions_dir="app/sessions"):
        self.sessions_dir = Path(sessions_dir)
        self.sessions_dir.mkdir(parents=True, exist_ok=True)

    def create_session(self, title="New Chat"):
        session_id = str(uuid.uuid4())
        session_data = {
            "id": session_id,
            "title": title,
            "created_at": datetime.now().isoformat(),
            "history": []
        }
        self._save_session(session_id, session_data)
        return session_id, session_data

    def get_session(self, session_id):
        path = self.sessions_dir / f"{session_id}.json"
        if path.exists():
            with open(path, "r") as f:
                return json.load(f)
        return None

    def list_sessions(self):
        sessions = []
        for f in self.sessions_dir.glob("*.json"):
            try:
                with open(f, "r") as file:
                    data = json.load(file)
                    sessions.append({
                        "id": data["id"],
                        "title": data.get("title", "Untitled"),
                        "created_at": data.get("created_at", "")
                    })
            except:
                pass
        # Sort by date desc
        return sorted(sessions, key=lambda x: x["created_at"], reverse=True)

    def update_session(self, session_id, history, title=None):
        data = self.get_session(session_id)
        if data:
            data["history"] = history
            if title:
                data["title"] = title
            self._save_session(session_id, data)

    def delete_session(self, session_id):
        path = self.sessions_dir / f"{session_id}.json"
        if path.exists():
            path.unlink()

    def _save_session(self, session_id, data):
        with open(self.sessions_dir / f"{session_id}.json", "w") as f:
            json.dump(data, f, indent=2)

    def cleanup_empty_sessions(self):
        count = 0
        for f in self.sessions_dir.glob("*.json"):
            try:
                with open(f, "r") as file:
                    data = json.load(file)
                    if not data.get("history"):
                        file.unlink()
                        count += 1
            except:
                pass
        return count

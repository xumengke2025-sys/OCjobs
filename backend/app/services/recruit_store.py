import json
import os
import random
import threading
import time
import uuid
from typing import Optional


class RecruitStore:
    def __init__(self):
        base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
        data_dir = os.path.join(base_dir, 'data')
        os.makedirs(data_dir, exist_ok=True)
        self.path = os.path.join(data_dir, 'recruit_store.json')
        self._lock = threading.Lock()

    def _load(self) -> dict:
        if not os.path.exists(self.path):
            return {"resumes": {}, "applications": {}, "chats": {}}
        with open(self.path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        data.setdefault("resumes", {})
        data.setdefault("applications", {})
        data.setdefault("chats", {})
        return data

    def _save(self, data: dict) -> None:
        tmp = self.path + ".tmp"
        with open(tmp, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        os.replace(tmp, self.path)

    def upsert_resume(self, resume_id: str, resume: dict) -> dict:
        with self._lock:
            data = self._load()
            data["resumes"][resume_id] = {
                "id": resume_id,
                "resume": resume,
                "created_at": data["resumes"].get(resume_id, {}).get("created_at") or int(time.time()),
                "updated_at": int(time.time())
            }
            self._save(data)
            return data["resumes"][resume_id]

    def get_resume(self, resume_id: str) -> Optional[dict]:
        with self._lock:
            data = self._load()
            return data["resumes"].get(resume_id)

    def create_application(self, resume_id: str, company: dict) -> dict:
        app_id = str(uuid.uuid4())
        now = int(time.time())
        contact_type = random.choice(["hr", "headhunter"])
        with self._lock:
            data = self._load()
            data["applications"][app_id] = {
                "id": app_id,
                "resume_id": resume_id,
                "company_id": company["id"],
                "company_name": company["name"],
                "contact_type": contact_type,
                "status": "applied",
                "created_at": now,
                "updated_at": now
            }
            self._save(data)
            return data["applications"][app_id]

    def get_application(self, application_id: str) -> Optional[dict]:
        with self._lock:
            data = self._load()
            return data["applications"].get(application_id)

    def list_applications(self, resume_id: Optional[str] = None) -> list:
        with self._lock:
            data = self._load()
            apps = list(data["applications"].values())
        if resume_id:
            apps = [a for a in apps if a.get("resume_id") == resume_id]
        apps.sort(key=lambda x: x.get("created_at", 0), reverse=True)
        return apps

    def get_or_create_chat(self, application: dict) -> dict:
        app_id = application["id"]
        with self._lock:
            data = self._load()
            if app_id in data["chats"]:
                return data["chats"][app_id]
            chat_id = str(uuid.uuid4())
            data["chats"][app_id] = {
                "id": chat_id,
                "application_id": app_id,
                "company_id": application.get("company_id"),
                "company_name": application.get("company_name"),
                "contact_type": application.get("contact_type") or "hr",
                "created_at": int(time.time()),
                "messages": []
            }
            self._save(data)
            return data["chats"][app_id]

    def list_chat_messages(self, application_id: str) -> list:
        with self._lock:
            data = self._load()
            chat = data["chats"].get(application_id)
            if not chat:
                return []
            return list(chat.get("messages") or [])

    def append_chat_message(self, application_id: str, role: str, content: str) -> dict:
        now = int(time.time())
        with self._lock:
            data = self._load()
            chat = data["chats"].get(application_id)
            if not chat:
                app = data["applications"].get(application_id)
                if not app:
                    raise ValueError("application_id 不存在")
                chat = {
                    "id": str(uuid.uuid4()),
                    "application_id": application_id,
                    "company_id": app.get("company_id"),
                    "company_name": app.get("company_name"),
                    "contact_type": app.get("contact_type") or "hr",
                    "created_at": now,
                    "messages": []
                }
                data["chats"][application_id] = chat
            chat.setdefault("messages", [])
            chat["messages"].append({"role": role, "content": content, "ts": now})
            self._save(data)
            return chat


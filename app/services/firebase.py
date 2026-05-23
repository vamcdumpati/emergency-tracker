import os, json, firebase_admin
from firebase_admin import credentials, auth
from fastapi import HTTPException

_app = None

def get_firebase_app():
    global _app
    if _app is not None:
        return _app
    creds_json = os.environ.get("FIREBASE_CREDENTIALS_JSON")
    if creds_json:
        cred = credentials.Certificate(json.loads(creds_json))
        _app = firebase_admin.initialize_app(cred)
        return _app
    raise RuntimeError("Set FIREBASE_CREDENTIALS_JSON env var")

def verify_firebase_token(id_token: str) -> dict:
    try:
        get_firebase_app()
        return auth.verify_id_token(id_token)
    except Exception as e:
        raise HTTPException(status_code=401, detail=str(e))

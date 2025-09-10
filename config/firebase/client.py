# config/firebase/client.py
import firebase_admin
from firebase_admin import credentials, firestore, db
from config.paths import get_credentials_path, DATABASE_URL

# Inicializa uma única vez
if not firebase_admin._apps:
    try:
        cred = credentials.Certificate(get_credentials_path())
        firebase_admin.initialize_app(cred, {"databaseURL": DATABASE_URL})
    except Exception as e:
        raise RuntimeError(f"🚫 Erro ao inicializar Firebase: {e}")

# Exports (mantém nomes que já usamos no projeto)
firestore_db = firestore.client()
realtime_db = db.reference()

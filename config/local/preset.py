# config/local/preset.py
from config.firebase.client import firestore_db


def carregar_preset(planta: str, fase: str) -> dict | None:
    try:
        doc = (
            firestore_db.collection("Presets")
            .document(planta)
            .collection(fase)
            .document("Padrao")
            .get()
        )
        return doc.to_dict() if doc.exists else None
    except Exception as e:
        print(f"⚠️ Erro ao carregar preset {planta}/{fase}: {e}")
        return None

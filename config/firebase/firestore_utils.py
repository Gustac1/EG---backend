# config/firebase/firestore_utils.py
import time
from firebase_admin import firestore as _firestore
from .client import firestore_db


def enviar_dados_firestore(estufa_id: str, dados: dict) -> bool:
    """
    Envia médias dos sensores para o Firestore em coleções por sensor.
    """
    try:
        batch = firestore_db.batch()
        timestamp = _firestore.SERVER_TIMESTAMP

        sensores = {k: v for k, v in dados.items() if k != "timestamp"}
        for sensor, valor in sensores.items():
            doc_ref = (
                firestore_db.collection("Dispositivos")
                .document(estufa_id)
                .collection("Dados")
                .document(sensor)
                .collection("Historico")
                .document()
            )
            batch.set(doc_ref, {f"{sensor}Atual": valor, "timestamp": timestamp})

        batch.commit()
        print(f"✅ Firestore: Histórico atualizado para {estufa_id}")
        return True
    except Exception as e:
        print(f"⚠️ Erro ao enviar dados para Firestore: {e}")
        return False


def atualizar_status_atuador(
    estufa_id: str, nome_atuador: str, ligado: bool, motivo: str
) -> bool:
    """
    Atualiza status/motivo do atuador em Dispositivos/{estufa_id}/Dados/{nome_atuador}.
    """
    try:
        doc_ref = (
            firestore_db.collection("Dispositivos")
            .document(estufa_id)
            .collection("Dados")
            .document(nome_atuador)
        )
        doc_ref.set({"Estado": ligado, "Motivo": motivo}, merge=True)
        return True
    except Exception as e:
        print(f"⚠️ Erro ao atualizar atuador {nome_atuador}: {e}")
        return False

# config/firebase/realtime_utils.py
from .client import realtime_db


def enviar_dados_realtime(estufa_id: str, dados: dict) -> bool:
    """
    Atualiza os valores atuais dos sensores no Realtime Database.
    """
    try:
        ref = realtime_db.child(f"Dispositivos/{estufa_id}/DadosAtuais")
        ref.update(dados)
        return True
    except Exception as e:
        print(f"⚠️ Erro ao enviar dados para Realtime DB: {e}")
        return False

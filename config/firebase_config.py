# config/firebase_config.py

import firebase_admin
from firebase_admin import credentials, firestore, db

# 🔥 Caminho para o arquivo de credenciais
# Preferencialmente definido pela variável de ambiente FIREBASE_CREDENTIALS
# 🔥 Caminho fixo para o arquivo de credenciais
CREDENCIAIS_PATH = "/home/TCCGustavo/Documents/EG - backend/config/credentials/ecogrowth-772d4-firebase-adminsdk-ubo79-eef9fa5c2f.json"

# 🔥 Inicialização do Firebase (somente uma vez por execução)
if not firebase_admin._apps:
    try:
        cred = credentials.Certificate(CREDENCIAIS_PATH)
        firebase_admin.initialize_app(
            cred,
            {"databaseURL": "https://ecogrowth-772d4-default-rtdb.firebaseio.com/"},
        )
    except Exception as e:
        raise RuntimeError(f"🚫 Erro ao inicializar Firebase: {e}")

# 🔥 Conexões globais
firestore_db = firestore.client()
realtime_db = db.reference()


def enviar_dados_realtime(estufa_id, dados):
    """
    Atualiza os valores atuais dos sensores no Realtime Database.

    Parâmetros:
        estufa_id (str): Identificador único da estufa.
        dados (dict): Leituras atuais dos sensores.

    Retorna:
        bool: True se envio bem-sucedido, False caso contrário.
    """
    try:
        ref = realtime_db.child(f"Dispositivos/{estufa_id}/DadosAtuais")
        ref.update(dados)
        return True
    except Exception as e:
        print(f"⚠️ Erro ao enviar dados para Realtime DB: {e}")
        return False


def enviar_dados_firestore(estufa_id, dados):
    """
    Envia os dados médios dos sensores para o Firestore (como histórico).

    Parâmetros:
        estufa_id (str): Identificador único da estufa.
        dados (dict): Médias calculadas dos sensores.

    Retorna:
        bool: True se envio bem-sucedido, False caso contrário.
    """
    try:
        batch = firestore_db.batch()
        timestamp = firestore.SERVER_TIMESTAMP

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


def atualizar_status_atuador(estufa_id, nome_atuador, ligado, motivo):
    """
    Atualiza o status de um atuador no Firestore.

    Estrutura gravada:
        Dispositivos/{estufa_id}/Dados/{nome_atuador}

    Parâmetros:
        estufa_id (str): Identificador único da estufa.
        nome_atuador (str): Nome do atuador (ex.: "Aquecedor").
        ligado (bool): Estado atual (True = ligado, False = desligado).
        motivo (str): Motivo do estado atual.

    Retorna:
        bool: True se atualização bem-sucedida, False caso contrário.
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

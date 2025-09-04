import firebase_admin
from firebase_admin import credentials, firestore, db

# 🔥 Caminho para o arquivo de credenciais do Firebase Admin SDK
# Certifique-se de que o caminho esteja correto e que o arquivo JSON contenha as permissões necessárias
CREDENCIAIS_PATH = "/home/TCCGustavo/Documents/EG - backend/Config/Credentials/ecogrowth-772d4-firebase-adminsdk-ubo79-eef9fa5c2f.json"

# 🔥 Inicialização do Firebase (ocorre apenas se ainda não estiver inicializado)
# Isso previne múltiplas inicializações quando este módulo é importado por outros scripts
if not firebase_admin._apps:
    cred = credentials.Certificate(CREDENCIAIS_PATH)
    firebase_admin.initialize_app(
        cred,
        {
            "databaseURL": "https://ecogrowth-772d4-default-rtdb.firebaseio.com/"  # URL do Realtime Database
        },
    )

# 🔥 Criação de conexões com Firestore e Realtime Database
firestore_db = firestore.client()
realtime_db = db.reference()


def enviar_dados_realtime(estufa_id, dados):
    """
    Atualiza os valores atuais dos sensores no Realtime Database do Firebase.
    - estufa_id: Identificador único da estufa (ex: 'EG001')
    - dados: Dicionário contendo os valores atuais lidos dos sensores

    Retorna True em caso de sucesso, False em caso de falha.
    """
    try:
        ref = realtime_db.child(f"Dispositivos/{estufa_id}/DadosAtuais")
        ref.update(dados)
        return True
    except Exception as e:
        print(f"❌ [Realtime] Erro: {e}")
        return False


def enviar_dados_firestore(estufa_id, dados):
    """
    Envia os dados médios dos sensores para o Firestore (como histórico).
    - estufa_id: Identificador único da estufa
    - dados: Dicionário contendo médias calculadas dos sensores, com timestamp incluso

    Para cada sensor, cria um novo documento na subcoleção "Historico" do sensor correspondente.
    Retorna True em caso de sucesso, False em caso de falha.
    """
    try:
        batch = firestore_db.batch()
        timestamp = firestore.SERVER_TIMESTAMP

        for sensor, valor in dados.items():
            if sensor != "timestamp":
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
        return True
    except Exception as e:
        print(f"❌ [Firestore] Erro: {e}")
        return False


def atualizar_status_atuador(
    estufa_id: str, nome_atuador: str, ligado: bool, motivo: str
):
    """
    Atualiza o status de um atuador no Firestore.
    Exemplo de caminho: Dispositivos/EG001/Dados/Aquecedor
    """
    try:
        doc_ref = (
            firestore_db.collection("Dispositivos")
            .document(estufa_id)
            .collection("Dados")
            .document(nome_atuador)
        )

        doc_ref.set(
            {
                "Estado": ligado,
                "Motivo": motivo,
            },
            merge=True,
        )

        print(
            f"✅ Firestore: {nome_atuador} {'LIGADO' if ligado else 'DESLIGADO'} | Motivo: {motivo}"
        )

    except Exception as e:
        print(f"🚫 Erro ao atualizar {nome_atuador}: {e}")

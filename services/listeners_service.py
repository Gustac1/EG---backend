# services/listeners_service.py
from google.cloud import firestore
from config.firebase.client import firestore_db
from services.acoes.iniciar import iniciar_estufa
from services.acoes.reiniciar import reiniciar_estufa
from services.acoes.avancar import avancar_fase_forcado
from services.calibragem_service import (
    iniciar_calibragem_luminosidade,
    finalizar_calibragem_luminosidade,
)


def escutar_solicitacao_iniciar(estufa_id):
    """
    Listener para a solicitação de início da estufa.

    Monitora o documento:
        Dispositivos/{estufa_id}/Solicitacoes/Iniciar

    Quando "Status" == "pending":
      1. Chama a função `iniciar_estufa` passando a planta e a fase desejadas.
      2. Atualiza a solicitação para "confirmed" se tudo ocorrer bem.
      3. Caso ocorra erro, atualiza para "error" e registra a mensagem.

    Parâmetros:
        estufa_id (str): Identificador único da estufa.
    """
    doc_ref = (
        firestore_db.collection("Dispositivos")
        .document(estufa_id)
        .collection("Solicitacoes")
        .document("Iniciar")
    )

    def callback(doc_snapshot, changes, read_time):
        for doc in doc_snapshot:
            dados = doc.to_dict()
            if not dados:
                return

            if dados.get("Status") == "pending":
                try:
                    iniciar_estufa(estufa_id, dados.get("Planta"), dados.get("Fase"))

                    # Confirma solicitação
                    doc_ref.update({"Status": "confirmed", "MensagemErro": None})

                except Exception as e:
                    # Marca erro
                    doc_ref.update({"Status": "error", "MensagemErro": str(e)})
                    print(f"⚠️ Erro ao iniciar estufa {estufa_id}: {e}")

    # Ativa o listener em tempo real
    doc_ref.on_snapshot(callback)


def escutar_solicitacao_reiniciar(estufa_id):
    """
    Listener para a solicitação de reinício da estufa.

    Monitora:
        Dispositivos/{estufa_id}/Solicitacoes/Reiniciar

    Quando "Status" == "pending":
      1. Chama `reiniciar_estufa` para atualizar o Firestore e resetar o ciclo.
      2. Atualiza a solicitação para "confirmed" se tudo ocorrer bem.
      3. Caso ocorra erro, atualiza para "error" com a mensagem.
    """
    doc_ref = (
        firestore_db.collection("Dispositivos")
        .document(estufa_id)
        .collection("Solicitacoes")
        .document("Reiniciar")
    )

    def callback(doc_snapshot, changes, read_time):
        for doc in doc_snapshot:
            dados = doc.to_dict()
            if not dados:
                return

            if dados.get("Status") == "pending":
                try:
                    reiniciar_estufa(estufa_id)

                    # Confirma solicitação
                    doc_ref.update({"Status": "confirmed", "MensagemErro": None})

                except Exception as e:
                    doc_ref.update({"Status": "error", "MensagemErro": str(e)})
                    print(f"⚠️ Erro ao reiniciar estufa {estufa_id}: {e}")

    doc_ref.on_snapshot(callback)


def escutar_solicitacao_avancar(estufa_id):
    """
    Listener para a solicitação de avanço forçado da fase da estufa.

    Monitora:
        Dispositivos/{estufa_id}/Solicitacoes/AvancarEtapa

    Quando "Status" == "pending":
      1. Chama `avancar_fase_forcado`.
      2. Atualiza solicitação para "confirmed".
      3. Em caso de erro, atualiza para "error" com a mensagem.
    """
    doc_ref = (
        firestore_db.collection("Dispositivos")
        .document(estufa_id)
        .collection("Solicitacoes")
        .document("AvancarEtapa")
    )

    def callback(doc_snapshot, changes, read_time):
        for doc in doc_snapshot:
            dados = doc.to_dict()
            if not dados:
                return

            if dados.get("Status") == "pending":
                try:
                    avancar_fase_forcado(estufa_id)
                    doc_ref.update({"Status": "confirmed", "MensagemErro": None})
                except Exception as e:
                    doc_ref.update({"Status": "error", "MensagemErro": str(e)})
                    print(f"⚠️ Erro ao avançar fase da estufa {estufa_id}: {e}")

    doc_ref.on_snapshot(callback)


def escutar_solicitacao_calibragem(estufa_id, sensor_luminosidade):
    """
    Listener em tempo real no Firestore para ativar/desativar calibragem.
    """
    doc_ref = (
        firestore_db.collection("Dispositivos")
        .document(estufa_id)
        .collection("Solicitacoes")
        .document("Calibragem")
    )

    def on_snapshot(doc_snapshot, changes, read_time):
        for doc in doc_snapshot:
            dados = doc.to_dict() or {}
            calibragem = dados.get("CalibragemLuminosidade", False)

            if calibragem:
                iniciar_calibragem_luminosidade(sensor_luminosidade, estufa_id)
            else:
                finalizar_calibragem_luminosidade()

    doc_ref.on_snapshot(on_snapshot)

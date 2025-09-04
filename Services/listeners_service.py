# Services/listeners_service.py
from Utils.logger import warn
from Config.firebase_config import firestore_db
from Config.configuracao_local import carregar_configuracao_local, carregar_preset
from google.cloud import firestore
from Services.iniciar_estufa import iniciar_estufa
from Services.reiniciar_estufa import reiniciar_estufa
from Services.avancar_fase_forcado import avancar_fase_forcado
from Services.ciclo_estufa_service import ciclo_reset_event


from Config.firebase_config import firestore_db
from Services.ciclo_estufa_service import ciclo_reset_event


def escutar_overrides_desejados(estufa_id):
    """
    Cria um listener separado para cada variável com override.
    Isso garante que o callback só dispara quando aquele campo muda.

    Regras:
      - Só dispara se a estufa estiver ativa (EstadoSistema=True)
        e em fase operacional (≠ Standby, ≠ Colheita).
      - Quando o campo muda (True ou False), reseta o ciclo.
    """
    variaveis = [
        "Temperatura",
        "TemperaturaDoSolo",
        "Umidade",
        "UmidadeDoSolo",
        "Luminosidade",
        "Ventilacao",
    ]

    for variavel in variaveis:
        campo_override = f"Override{variavel}"

        doc_ref = (
            firestore_db.collection("Dispositivos")
            .document(estufa_id)
            .collection("Dados")
            .document(variavel)
        )

        def callback(
            doc_snapshot,
            changes,
            read_time,
            variavel=variavel,
            campo_override=campo_override,
        ):
            try:
                doc_estufa = (
                    firestore_db.collection("Dispositivos").document(estufa_id).get()
                )
                if not doc_estufa.exists:
                    return

                dados_estufa = doc_estufa.to_dict()
                fase = dados_estufa.get("FaseAtual")
                ativo = dados_estufa.get("EstadoSistema", False)

                if not ativo or fase in ("Standby", "Colheita"):
                    print(
                        f"ℹ️ Override ignorado para {variavel} (fase={fase}, ativo={ativo})"
                    )
                    return

                if campo_override in dados_estufa:
                    valor = dados_estufa[campo_override]
                    print(f"🔄 Override atualizado: {campo_override} = {valor}")
                    ciclo_reset_event.set()

            except Exception as e:
                print(f"[ERRO] Listener de override '{variavel}' falhou: {e}")

        doc_ref.on_snapshot(callback)


def escutar_solicitacao_iniciar(estufa_id):
    """
    Listener para a solicitação de início da estufa.

    Esse listener monitora o documento:
        Dispositivos/{estufa_id}/Solicitacoes/Iniciar

    Quando o campo "Status" é alterado para "pending":
      1. Chama a função `iniciar_estufa` passando a planta e a fase desejadas.
      2. Atualiza a solicitação para "confirmed" se tudo ocorrer bem.
      3. Caso ocorra erro, atualiza a solicitação para "error"
         e registra a mensagem de erro.

    Parâmetros:
        estufa_id (str): Identificador único da estufa.

    Retorna:
        None
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
                    iniciar_estufa(
                        estufa_id,
                        dados.get("Planta"),
                        dados.get("Fase"),
                    )

                    # Confirma solicitação
                    doc_ref.update({"Status": "confirmed", "MensagemErro": None})

                except Exception as e:
                    # Marca erro na solicitação
                    doc_ref.update({"Status": "error", "MensagemErro": str(e)})
                    print(f"[ERRO] Falha ao iniciar estufa {estufa_id}: {e}")

    # Ativa o listener em tempo real
    doc_ref.on_snapshot(callback)


def escutar_solicitacao_reiniciar(estufa_id):
    """
    Listener para a solicitação de reinício da estufa.

    Esse listener monitora o documento:
        Dispositivos/{estufa_id}/Solicitacoes/Reiniciar

    Quando o campo "Status" é alterado para "pending":
      1. Chama a função `reiniciar_estufa` para atualizar o Firestore
         e resetar o ciclo da estufa.
      2. Atualiza a solicitação para "confirmed" se tudo ocorrer bem.
      3. Caso ocorra erro, atualiza a solicitação para "error"
         e registra a mensagem de erro.

    Parâmetros:
        estufa_id (str): Identificador único da estufa.

    Retorna:
        None
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
                    # Marca erro na solicitação
                    doc_ref.update({"Status": "error", "MensagemErro": str(e)})
                    print(f"[ERRO] Falha ao reiniciar estufa {estufa_id}: {e}")

    # Ativa o listener em tempo real
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
                    print(f"[ERRO] Falha ao avançar fase da estufa {estufa_id}: {e}")

    doc_ref.on_snapshot(callback)

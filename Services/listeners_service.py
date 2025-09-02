# Services/listeners_service.py
from Utils.logger import warn
from Config.firebase_config import firestore_db
from Config.configuracao_local import carregar_configuracao_local, carregar_preset
from google.cloud import firestore
from Services.controle_service import rodar_controle_once
from Services.controle_service import desligar_todos_atuadores

def escutar_alteracoes_configuracao(estufa_id):
    """Escuta alterações na configuração da estufa no Firestore."""
    def callback(doc_snapshot, changes, read_time):
        for doc in doc_snapshot:
            nova_config = carregar_configuracao_local(estufa_id)
            if not nova_config:
                warn("Falha ao atualizar configuração local.")

    doc_ref = firestore_db.collection("Dispositivos").document(estufa_id)
    doc_ref.on_snapshot(callback)


def escutar_overrides_desejados(estufa_id):
    """Escuta alterações nos overrides individuais de cada variável."""
    variaveis = ["Temperatura", "TemperaturaDoSolo", "Umidade", "UmidadeDoSolo", "Luminosidade"]

    for variavel in variaveis:
        doc_ref = firestore_db.collection("Dispositivos").document(estufa_id).collection("Dados").document(variavel)

        def callback(doc_snapshot, changes, read_time, variavel=variavel):
            try:
                doc_estufa = firestore_db.collection("Dispositivos").document(estufa_id).get()
                if not doc_estufa.exists:
                    return

                dados_estufa = doc_estufa.to_dict()
                campo_override = f"Override{variavel}"

                if dados_estufa.get(campo_override, False):
                    nova_config = carregar_configuracao_local(estufa_id)
                    if not nova_config:
                        warn(f"Erro ao atualizar config após mudança em '{variavel}'")
            except Exception as e:
                warn(f"Erro no listener de override '{variavel}': {e}")

        doc_ref.on_snapshot(callback)


def escutar_solicitacao_iniciar(estufa_id, ventoinha, luminaria, bomba, aquecedor,
                                temperatura_ar_sensor, umidade_solo_sensor,
                                exibir_status_atuadores=None, exibir_status_fase=None):

    doc_ref = firestore_db.collection("Dispositivos").document(estufa_id).collection("Solicitacoes").document("Iniciar")

    def callback(doc_snapshot, changes, read_time):
        for doc in doc_snapshot:
            dados = doc.to_dict()
            if not dados:
                return

            if dados.get("Status") == "pending":
                try:
                    planta = dados.get("Planta")
                    fase = dados.get("Fase")

                    # valida preset
                    preset = carregar_preset(planta, fase)
                    if not preset:
                        raise Exception("Preset não encontrado")

                    # atualiza estado da estufa no Firestore
                    firestore_db.collection("Dispositivos").document(estufa_id).update({
                        "PlantaAtual": planta,
                        "FaseAtual": fase,
                        "InicioFaseTimestamp": firestore.SERVER_TIMESTAMP,
                        "EstadoSistema": True
                    })

                    # confirma solicitação
                    doc_ref.update({"Status": "confirmed", "MensagemErro": None})

                    # recarrega config local
                    carregar_configuracao_local(estufa_id)

                    # 🚀 rodada imediata de controle
                    rodar_controle_once(estufa_id, ventoinha, luminaria, bomba, aquecedor,
                                        temperatura_ar_sensor, umidade_solo_sensor,
                                        exibir_status_atuadores, exibir_status_fase)

                except Exception as e:
                    doc_ref.update({"Status": "error", "MensagemErro": str(e)})
                    warn(f"Erro ao iniciar: {e}")

    doc_ref.on_snapshot(callback)



def escutar_solicitacao_reiniciar(estufa_id, ventoinha, luminaria, bomba, aquecedor,
                                  exibir_status_atuadores=None, exibir_status_fase=None):
    doc_ref = firestore_db.collection("Dispositivos").document(estufa_id).collection("Solicitacoes").document("Reiniciar")

    def callback(doc_snapshot, changes, read_time):
        for doc in doc_snapshot:
            dados = doc.to_dict()
            if not dados:
                return

            if dados.get("Status") == "pending":
                try:
                    firestore_db.collection("Dispositivos").document(estufa_id).update({
                        "PlantaAtual": "Standby",
                        "FaseAtual": "Standby",
                        "InicioFaseTimestamp": None,
                        "EstadoSistema": False,
                        "ForcarAvancoFase": False
                    })

                    doc_ref.update({"Status": "confirmed", "MensagemErro": None})

                    # 🚀 desliga imediatamente
                    desligar_todos_atuadores(estufa_id, ventoinha, luminaria, bomba, aquecedor,
                                             exibir_status_atuadores, exibir_status_fase)

                except Exception as e:
                    doc_ref.update({"Status": "error", "MensagemErro": str(e)})
                    warn(f"Erro ao reiniciar: {e}")

    doc_ref.on_snapshot(callback)


def escutar_solicitacao_avancar(estufa_id):
    doc_ref = firestore_db.collection("Dispositivos").document(estufa_id).collection("Solicitacoes").document("AvancarEtapa")

    def callback(doc_snapshot, changes, read_time):
        for doc in doc_snapshot:
            dados = doc.to_dict()
            if not dados:
                return

            if dados.get("Status") == "pending":
                try:
                    firestore_db.collection("Dispositivos").document(estufa_id).update({"ForcarAvancoFase": True})
                    doc_ref.update({"Status": "confirmed", "MensagemErro": None})
                except Exception as e:
                    doc_ref.update({"Status": "error", "MensagemErro": str(e)})
                    warn(f"Erro ao processar avanço: {e}")

    doc_ref.on_snapshot(callback)

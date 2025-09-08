from config.firebase_config import firestore_db
from services.ciclo_service import ciclo_reset_event
from google.cloud import firestore
from services.fases_service import proxima_fase
from config.configuracao_local import carregar_configuracao_local


def avancar_fase_forcado(estufa_id):
    """
    Avança imediatamente a estufa para a próxima fase,
    independentemente do tempo decorrido.

    Fluxo:
      1. Carrega a configuração atual da estufa.
      2. Determina a próxima fase com base na fase atual.
      3. Atualiza o Firestore com:
         - Nova fase
         - InicioFaseTimestamp = agora
         - EstadoSistema = False se for Colheita, True caso contrário
      4. Reseta o ciclo para rodar imediatamente.
      5. Exibe mensagem de confirmação no terminal.
    """
    config = carregar_configuracao_local(estufa_id)
    if not config:
        raise Exception("Configuração local não encontrada.")

    fase_atual = config.get("FaseAtual")
    nova_fase = proxima_fase(fase_atual)
    if not nova_fase:
        raise Exception(f"Não há próxima fase para '{fase_atual}'.")

    firestore_db.collection("Dispositivos").document(estufa_id).update(
        {
            "FaseAtual": nova_fase,
            "InicioFaseTimestamp": firestore.SERVER_TIMESTAMP,
            "EstadoSistema": False if nova_fase == "Colheita" else True,
        }
    )

    # força rodada imediata
    ciclo_reset_event.set()

    print(f"⏩ Estufa {estufa_id} avançada forçadamente para fase '{nova_fase}'.")

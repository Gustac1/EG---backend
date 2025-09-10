from config.firebase.client import firestore_db
from utils.eventos import ciclo_reset_event
from google.cloud import firestore
from services.fases_service import proxima_fase, agendar_avanco_fase
from config.local.loader import carregar_configuracao_local


def avancar_fase_forcado(estufa_id: str) -> None:
    """
    Avança imediatamente a estufa para a próxima fase, ignorando o tempo decorrido.

    Este método é chamado quando o usuário solicita avanço manual via listener.
    Atualiza diretamente o Firestore e dispara o reset do ciclo principal.

    Fluxo:
        1. Carrega a configuração atual da estufa.
        2. Determina a próxima fase com base na fase atual.
        3. Atualiza o documento principal em Firestore:
            - FaseAtual → nova fase.
            - InicioFaseTimestamp → horário atual (servidor).
            - EstadoSistema → False se for Colheita, True caso contrário.
        4. Dispara o evento `ciclo_reset_event`, forçando o ciclo principal
           a rodar imediatamente com a nova configuração.
        5. Agenda o próximo avanço automático (threading.Timer).
        6. Exibe mensagem de confirmação no terminal.

    Parâmetros:
        estufa_id (str): Identificador único da estufa (ex.: "EG001").

    Retorna:
        None

    Exceções:
        - Levanta Exception se não houver configuração local válida
          ou se a fase atual não tiver próxima fase definida.
    """
    # 1. Carrega configuração atual
    config = carregar_configuracao_local(estufa_id)
    if not config:
        raise Exception("Configuração local não encontrada.")

    fase_atual = config.get("FaseAtual")
    nova_fase = proxima_fase(fase_atual)
    if not nova_fase:
        raise Exception(f"Não há próxima fase para '{fase_atual}'.")

    # 2. Atualiza Firestore com a nova fase
    firestore_db.collection("Dispositivos").document(estufa_id).update(
        {
            "FaseAtual": nova_fase,
            "InicioFaseTimestamp": firestore.SERVER_TIMESTAMP,
            "EstadoSistema": False if nova_fase == "Colheita" else True,
        }
    )

    # 3. Reseta ciclo → força o loop a rodar imediatamente
    ciclo_reset_event.set()

    # 4. Agenda avanço automático para o final da nova fase
    agendar_avanco_fase(estufa_id)

    # 5. Log de confirmação
    print(f"⏩ Estufa {estufa_id} avançada forçadamente para fase '{nova_fase}'.")

from config.firebase_config import firestore_db
from services.ciclo_service import ciclo_reset_event
from services.fases_service import cancelar_avanco_fase


def reiniciar_estufa(estufa_id: str) -> None:
    """
    Reinicia a estufa, retornando para o estado "Standby".

    Este método é chamado quando o usuário solicita um reinício via listener.
    Ele não desliga os atuadores diretamente: apenas marca o estado como
    Standby no Firestore e dispara o reset do ciclo principal. Na rodada
    seguinte, o ciclo detecta Standby e desliga todos os atuadores.

    Fluxo:
        1. Atualiza o documento principal no Firestore:
            - PlantaAtual = "Standby"
            - FaseAtual = "Standby"
            - InicioFaseTimestamp = None
            - EstadoSistema = False
            - ForcarAvancoFase = False
        2. Cancela qualquer avanço automático previamente agendado.
        3. Dispara o evento `ciclo_reset_event` para rodar o ciclo imediatamente.
        4. O ciclo, ao rodar, identifica Standby e desliga todos os atuadores.
        5. Exibe mensagem de confirmação no terminal.

    Parâmetros:
        estufa_id (str): Identificador único da estufa (ex.: "EG001").

    Retorna:
        None
    """
    # 1. Atualiza Firestore com estado de standby
    firestore_db.collection("Dispositivos").document(estufa_id).update(
        {
            "PlantaAtual": "Standby",
            "FaseAtual": "Standby",
            "InicioFaseTimestamp": None,
            "EstadoSistema": False,
            "ForcarAvancoFase": False,
        }
    )

    # 2. Cancela avanço automático pendente
    cancelar_avanco_fase()

    # 3. Reseta ciclo → força execução imediata
    ciclo_reset_event.set()

    # 4. Log de confirmação
    print(f"♻️ Estufa {estufa_id} reiniciada e colocada em Standby.")

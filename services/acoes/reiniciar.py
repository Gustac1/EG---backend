from config.firebase_config import firestore_db
from services.ciclo_service import ciclo_reset_event


def reiniciar_estufa(estufa_id):
    """
    Reinicia a estufa, retornando para o estado "Standby".

    Esse método é chamado quando o usuário solicita um reinício da estufa
    (via listener no Firestore). Ele não desliga os atuadores diretamente:
    em vez disso, marca a estufa como "Standby" no Firestore e reseta o ciclo.
    Na próxima rodada (imediata, devido ao reset), o ciclo principal irá:
      - Detectar que a fase/estado está em Standby.
      - Desligar todos os atuadores de forma centralizada pela lógica
        do `controlar_atuadores`.

    Fluxo:
        1. Atualiza o Firestore com os valores padrão de reinício:
            - PlantaAtual = "Standby"
            - FaseAtual = "Standby"
            - InicioFaseTimestamp = None
            - EstadoSistema = False
            - ForcarAvancoFase = False
        2. Dispara o evento `ciclo_reset_event` para que o ciclo principal rode imediatamente.
        3. O ciclo, ao rodar, identifica Standby e desliga todos os atuadores.
        4. Exibe mensagem de confirmação no terminal.

    Parâmetros:
        estufa_id (str): Identificador único da estufa.

    Retorna:
        None
    """
    # 1. Atualiza Firestore
    firestore_db.collection("Dispositivos").document(estufa_id).update(
        {
            "PlantaAtual": "Standby",
            "FaseAtual": "Standby",
            "InicioFaseTimestamp": None,
            "EstadoSistema": False,
            "ForcarAvancoFase": False,
        }
    )

    # 2. Reseta ciclo → força o ciclo a rodar imediatamente
    ciclo_reset_event.set()

    # 3. Log
    print(f"♻️ Estufa {estufa_id} reiniciada e colocada em Standby.")

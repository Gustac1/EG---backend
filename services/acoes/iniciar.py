from config.firebase_config import firestore_db
from google.cloud import firestore
from config.configuracao_local import carregar_preset
from services.ciclo_service import ciclo_reset_event


def iniciar_estufa(estufa_id, planta, fase):
    """
    Inicializa a estufa com base na planta e fase escolhidas.

    Fluxo:
      1. Valida o preset da planta/fase (se não existir, lança exceção).
      2. Atualiza o Firestore com os novos dados iniciais da estufa:
         - PlantaAtual
         - FaseAtual
         - InicioFaseTimestamp (servidor)
         - EstadoSistema = True
      3. Reseta o ciclo principal (através de um threading.Event),
         fazendo com que o ciclo rode imediatamente após a inicialização.
      4. Exibe mensagem de confirmação no terminal.

    Parâmetros:
        estufa_id (str): Identificador da estufa.
        planta (str): Nome da planta a cultivar.
        fase (str): Fase inicial ("Germinacao", "Crescimento", etc.).

    Retorna:
        None
    """
    # 1. Valida preset
    preset = carregar_preset(planta, fase)
    if not preset:
        raise Exception(f"Preset não encontrado para planta={planta}, fase={fase}")

    # 2. Atualiza Firestore
    firestore_db.collection("Dispositivos").document(estufa_id).update(
        {
            "PlantaAtual": planta,
            "FaseAtual": fase,
            "InicioFaseTimestamp": firestore.SERVER_TIMESTAMP,
            "EstadoSistema": True,
        }
    )

    # 3. Reset do ciclo → faz a thread do ciclo rodar na hora
    ciclo_reset_event.set()

    # 4. Confirma no terminal
    print(f"✅ Estufa {estufa_id} iniciada com planta={planta}, fase={fase}")

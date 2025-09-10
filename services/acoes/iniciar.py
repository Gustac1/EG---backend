from config.firebase_config import firestore_db
from google.cloud import firestore
from config.configuracao_local import carregar_preset
from services.ciclo_service import ciclo_reset_event
from services.fases_service import agendar_avanco_fase


def iniciar_estufa(estufa_id: str, planta: str, fase: str) -> None:
    """
    Inicializa a estufa com base na planta e fase escolhidas.

    Este método é chamado quando o usuário solicita o início do cultivo.
    Ele valida o preset, grava os dados iniciais no Firestore, reseta
    o ciclo principal e agenda o próximo avanço automático.

    Fluxo:
        1. Valida se existe preset da planta/fase escolhida.
        2. Atualiza o documento principal da estufa no Firestore:
            - PlantaAtual → planta escolhida.
            - FaseAtual → fase inicial escolhida.
            - InicioFaseTimestamp → timestamp do servidor.
            - EstadoSistema → True.
        3. Dispara o evento `ciclo_reset_event` para que o ciclo rode imediatamente.
        4. Agenda o avanço automático para o final da fase inicial.
        5. Exibe mensagem de confirmação no terminal.

    Parâmetros:
        estufa_id (str): Identificador da estufa (ex.: "EG001").
        planta (str): Nome da planta a cultivar.
        fase (str): Fase inicial ("Germinacao", "Crescimento", etc.).

    Retorna:
        None

    Exceções:
        - Levanta Exception se o preset da planta/fase não for encontrado.
    """
    # 1. Valida preset da planta/fase
    preset = carregar_preset(planta, fase)
    if not preset:
        raise Exception(f"Preset não encontrado para planta={planta}, fase={fase}")

    # 2. Atualiza Firestore com estado inicial
    firestore_db.collection("Dispositivos").document(estufa_id).update(
        {
            "PlantaAtual": planta,
            "FaseAtual": fase,
            "InicioFaseTimestamp": firestore.SERVER_TIMESTAMP,
            "EstadoSistema": True,
        }
    )

    # 3. Reseta ciclo → força execução imediata
    ciclo_reset_event.set()

    # 4. Agenda avanço automático da fase
    agendar_avanco_fase(estufa_id)

    # 5. Confirmação no terminal
    print(f"✅ Estufa {estufa_id} iniciada com planta={planta}, fase={fase}")

# Services/fase_service.py
import time
from datetime import datetime, timezone
from dateutil.parser import isoparse

from Config.firebase_config import firestore_db
from Config.configuracao_local import carregar_preset


def proxima_fase(fase_atual):
    """
    Retorna a próxima fase do ciclo de cultivo com base na ordem pré-definida.

    Ordem: Germinacao → Crescimento → Floracao → Colheita

    Parâmetros:
        fase_atual (str): Nome da fase atual.

    Retorna:
        str | None: Nome da próxima fase, ou None se já estiver em Colheita ou se fase for inválida.
    """
    ordem = ["Germinacao", "Crescimento", "Floracao", "Colheita"]
    if fase_atual in ordem:
        idx = ordem.index(fase_atual)
        return ordem[idx + 1] if idx + 1 < len(ordem) else None
    return None


def verificar_e_avancar_fase(estufa_id, config):
    """
    Verifica se a fase da estufa deve ser avançada com base apenas no tempo decorrido.
    O avanço forçado (ForcarAvancoFase) é tratado separadamente pelos listeners.

    Parâmetros:
        estufa_id (str): Identificador da estufa.
        config (dict): Configuração atual carregada pelo ciclo.

    Retorna:
        str | None: Nome da nova fase se houve avanço, ou None se nada mudou.
    """
    try:
        if not config:
            print("[ERRO] Configuração local não encontrada.")
            return None

        planta = config.get("PlantaAtual")
        fase = config.get("FaseAtual")
        inicio_ts = config.get("InicioFaseTimestamp")

        # Casos em que não há avanço
        if fase == "Standby" or planta == "Standby":
            return None
        if not planta or not fase or not inicio_ts:
            return None

        # Converte timestamp de início
        try:
            inicio_fase = isoparse(inicio_ts).astimezone(timezone.utc)
        except Exception:
            return None

        # Calcula dias corridos
        dias_corridos = (
            datetime.now(timezone.utc) - inicio_fase
        ).total_seconds() / 86400

        # Carrega preset da planta/fase atual
        preset = carregar_preset(planta, fase)
        if not preset:
            return None

        dias_necessarios = preset.get("DiasNaEtapa", 9999)

        # Ainda não completou a fase
        if dias_corridos < dias_necessarios:
            return None

        # Avança para próxima fase
        nova_fase = proxima_fase(fase)
        if not nova_fase:
            return None

        firestore_db.collection("Dispositivos").document(estufa_id).update(
            {
                "FaseAtual": nova_fase,
                "InicioFaseTimestamp": datetime.now(timezone.utc),
                "EstadoSistema": False if nova_fase == "Colheita" else True,
            }
        )

        return nova_fase

    except Exception as e:
        print(f"[ERRO] Falha ao avançar fase: {e}")
        return None

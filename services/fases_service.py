# services/fases_service.py
"""
Serviço de controle de fases da estufa.

Responsabilidades:
- Calcular a próxima fase de cultivo.
- Verificar e avançar automaticamente a fase com base no tempo decorrido.
- Agendar avanço automático exato (threading.Timer).
- Cancelar avanço automático em casos de reinício/standby.

Fluxo esperado:
- iniciar_estufa → agendar_avanco_fase
- avancar_fase_forcado → cancelar + agendar_avanco_fase
- reiniciar_estufa → cancelar_avanco_fase
- ciclo_estufa → verificar_e_avancar_fase (fallback de segurança)
"""

import threading
from datetime import datetime, timezone, timedelta
from dateutil.parser import isoparse

from config.firebase.client import firestore_db
from config.local.loader import carregar_configuracao_local, carregar_preset


# Timer global para avanço automático
_timer_fase = None


def cancelar_avanco_fase() -> None:
    """
    Cancela o timer de avanço automático, se existir.

    Usado em:
      - reiniciar_estufa
      - quando a estufa entra em standby ou colheita
    """
    global _timer_fase
    if _timer_fase:
        _timer_fase.cancel()
        _timer_fase = None
        print("🛑 Avanço automático cancelado (reinício/standby).")


def agendar_avanco_fase(estufa_id: str) -> None:
    """
    Agenda automaticamente o avanço para a próxima fase no horário exato,
    com base em InicioFaseTimestamp + DiasNaEtapa do preset.

    Parâmetros:
        estufa_id (str): Identificador único da estufa.

    Observações:
        - Se já passou do tempo previsto, não agenda (o ciclo normal avançará).
        - Substitui qualquer timer anterior (_timer_fase global).
        - Usa threading.Timer com função local `_avancar`.
    """
    global _timer_fase

    config = carregar_configuracao_local(estufa_id)
    if not config:
        return

    planta = config.get("PlantaAtual")
    fase = config.get("FaseAtual")
    inicio_ts = config.get("InicioFaseTimestamp")

    if not planta or not fase or not inicio_ts:
        return

    preset = carregar_preset(planta, fase)
    if not preset:
        return

    dias_na_etapa = preset.get("DiasNaEtapa")
    if not dias_na_etapa:
        return

    # Converte início para datetime UTC
    inicio = isoparse(inicio_ts).astimezone(timezone.utc)
    fim = inicio + timedelta(days=dias_na_etapa)
    agora = datetime.now(timezone.utc)

    segundos_restantes = (fim - agora).total_seconds()
    if segundos_restantes <= 0:
        return  # já deveria ter avançado → ciclo normal resolve

    # Cancela timer anterior, se existir
    if _timer_fase:
        _timer_fase.cancel()

    def _avancar():
        """
        Função interna executada pelo timer no momento exato.
        - Revalida config local
        - Chama verificar_e_avancar_fase
        - Se avançar, reseta ciclo e agenda próximo avanço
        """
        from services.ciclo_service import ciclo_reset_event, verificar_e_avancar_fase
        from config.local.loader import carregar_configuracao_local

        config_local = carregar_configuracao_local(estufa_id)
        nova = verificar_e_avancar_fase(estufa_id, config_local)
        if nova:
            print(f"⏩ Avanço agendado disparado: {nova}")
            ciclo_reset_event.set()
            agendar_avanco_fase(estufa_id)

    # Agenda execução exata
    _timer_fase = threading.Timer(segundos_restantes, _avancar)
    _timer_fase.daemon = True
    _timer_fase.start()

    print(f"⏳ Avanço agendado para {fim.isoformat()}")


def proxima_fase(fase_atual: str) -> str | None:
    """
    Retorna o nome da próxima fase do ciclo de cultivo.

    Ordem: Germinacao → Crescimento → Floracao → Colheita

    Parâmetros:
        fase_atual (str): Nome da fase atual.

    Retorna:
        str | None:
            - Nome da próxima fase, se existir.
            - None, se já estiver em Colheita ou fase inválida.
    """
    ordem = ["Germinacao", "Crescimento", "Floracao", "Colheita"]
    if fase_atual in ordem:
        idx = ordem.index(fase_atual)
        return ordem[idx + 1] if idx + 1 < len(ordem) else None
    return None


def verificar_e_avancar_fase(estufa_id: str, config: dict) -> str | None:
    """
    Verifica se a fase da estufa deve ser avançada com base no tempo decorrido.

    Fluxo:
      1. Lê PlantaAtual, FaseAtual e InicioFaseTimestamp.
      2. Calcula tempo corrido da fase.
      3. Compara com DiasNaEtapa do preset.
      4. Se tempo cumprido, atualiza Firestore para a próxima fase.

    Parâmetros:
        estufa_id (str): Identificador único da estufa.
        config (dict): Configuração atual carregada.

    Retorna:
        str | None:
            - Nome da nova fase se houve avanço.
            - None se não houve mudança.
    """
    try:
        if not config:
            print("🚫 Configuração local não encontrada.")
            return None

        planta = config.get("PlantaAtual")
        fase = config.get("FaseAtual")
        inicio_ts = config.get("InicioFaseTimestamp")

        if not planta or not fase or not inicio_ts:
            return None
        if fase == "Standby" or planta == "Standby":
            return None

        try:
            inicio_fase = isoparse(inicio_ts).astimezone(timezone.utc)
        except Exception:
            return None

        dias_corridos = (
            datetime.now(timezone.utc) - inicio_fase
        ).total_seconds() / 86400

        preset = carregar_preset(planta, fase)
        if not preset:
            return None

        dias_necessarios = preset.get("DiasNaEtapa", 9999)

        if dias_corridos < dias_necessarios:
            return None

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
        print(f"⚠️ Erro ao avançar fase: {e}")
        return None

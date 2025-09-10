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
- avancar_fase_forcado → agendar_avanco_fase
- reiniciar_estufa → cancelar_avanco_fase
- ciclo_estufa → verificar_e_avancar_fase (fallback de segurança)

Observação:
- O timer global (_timer_fase) considera uma estufa por processo.
  Para multiestufas, evoluir para um dicionário {estufa_id: Timer}.
"""

import threading
from datetime import datetime, timezone, timedelta
from dateutil.parser import isoparse
from google.cloud import firestore  # para SERVER_TIMESTAMP

from config.firebase.client import firestore_db
from config.local.loader import carregar_configuracao_local
from config.local.preset import carregar_preset
from utils.eventos import ciclo_reset_event


# Timer global para avanço automático (1 estufa por processo)
_timer_fase: threading.Timer | None = None


def cancelar_avanco_fase() -> None:
    """
    Cancela o timer de avanço automático, se existir.

    Usado em:
      - reiniciar_estufa
      - quando a estufa entra em Standby/Colheita
    """
    global _timer_fase
    if _timer_fase:
        _timer_fase.cancel()
        _timer_fase = None
        print("🛑 Avanço automático cancelado (reinício/standby/colheita).")


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
        print("⚠️ Não foi possível agendar: config local ausente.")
        return

    planta = config.get("PlantaAtual")
    fase = config.get("FaseAtual")
    inicio_ts = config.get("InicioFaseTimestamp")

    # Não agenda em Standby nem em Colheita
    if not planta or not fase or not inicio_ts or fase in ("Standby", "Colheita"):
        cancelar_avanco_fase()
        return

    preset = carregar_preset(planta, fase)
    if not preset:
        print(f"⚠️ Não foi possível agendar: preset ausente ({planta}/{fase}).")
        return

    dias_na_etapa = preset.get("DiasNaEtapa")
    if not dias_na_etapa:
        # se 0/None, não agenda (interpreta como fase sem tempo)
        print("⚠️ Não foi possível agendar: 'DiasNaEtapa' inválido.")
        return

    # Converte início para datetime UTC (aceita ISO string ou datetime)
    try:
        if isinstance(inicio_ts, datetime):
            inicio = (
                inicio_ts
                if inicio_ts.tzinfo
                else inicio_ts.replace(tzinfo=timezone.utc)
            )
            inicio = inicio.astimezone(timezone.utc)
        else:
            inicio = isoparse(inicio_ts).astimezone(timezone.utc)
    except Exception:
        print("⚠️ Não foi possível agendar: 'InicioFaseTimestamp' inválido.")
        return

    fim = inicio + timedelta(days=dias_na_etapa)
    agora = datetime.now(timezone.utc)

    segundos_restantes = (fim - agora).total_seconds()
    if segundos_restantes <= 0:
        # Já passou — o fallback do ciclo fará o avanço
        print("ℹ️ Tempo de fase já vencido; ciclo fará o avanço no próximo tick.")
        return

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

    print(f"⏳ Avanço agendado para {fim.isoformat()} (em ~{int(segundos_restantes)}s)")


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

        # Sem avanço em ausência de dados, Standby ou Colheita
        if not planta or not fase or not inicio_ts or fase in ("Standby", "Colheita"):
            return None

        # Converte timestamp de início
        try:
            if isinstance(inicio_ts, datetime):
                inicio_fase = (
                    inicio_ts
                    if inicio_ts.tzinfo
                    else inicio_ts.replace(tzinfo=timezone.utc)
                )
                inicio_fase = inicio_fase.astimezone(timezone.utc)
            else:
                inicio_fase = isoparse(inicio_ts).astimezone(timezone.utc)
        except Exception:
            return None

        # Calcula dias corridos desde o início da fase
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
                # Padroniza para timestamp do servidor (consistente com iniciar/avançar forçado)
                "InicioFaseTimestamp": firestore.SERVER_TIMESTAMP,
                "EstadoSistema": False if nova_fase == "Colheita" else True,
            }
        )

        return nova_fase

    except Exception as e:
        print(f"⚠️ Erro ao avançar fase: {type(e).__name__}: {e}")
        return None

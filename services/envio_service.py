import time
import threading
from datetime import datetime, timedelta
from config.firebase.firestore_utils import enviar_dados_firestore
from services.coleta_service import buffer_sensores  # reaproveita o mesmo buffer


# ================================
# 📊 Utilitário de cálculo
# ================================
def media(lista):
    """
    Calcula a média de uma lista numérica.
    Retorna None se a lista estiver vazia.
    """
    return sum(lista) / len(lista) if lista else None


# ================================
# ☁️ Envio de dados periódicos
# ================================
def enviar_dados_periodicamente(estufa_id, mostrar_no_terminal=False):
    """
    Executa uma rodada única de envio de médias dos sensores.

    Simplificação:
        - Sempre calcula a média (mesmo que vazia → None).
        - Sempre envia para o Firestore no disparo do scheduler.
        - Buffers são limpos após o envio.

    Retorna:
        True  → envio realizado com sucesso.
        False → erro durante o envio.
    """
    try:
        media_dados = {
            "Luminosidade": media(buffer_sensores["Luminosidade"]),
            "TemperaturaDoSolo": media(buffer_sensores["TemperaturaDoSolo"]),
            "Temperatura": media(buffer_sensores["Temperatura"]),
            "Umidade": media(buffer_sensores["Umidade"]),
            "UmidadeDoSolo": media(buffer_sensores["UmidadeDoSolo"]),
            "timestamp": round(time.time(), 2),
        }

        # 🔄 Limpa buffers
        for key in buffer_sensores:
            buffer_sensores[key].clear()

        # ☁️ Envia ao Firestore
        enviar_dados_firestore(estufa_id, media_dados)

        # 🖥️ Exibe no terminal (opcional)
        if mostrar_no_terminal:
            from utils.display import exibir_dados_periodicos

            exibir_dados_periodicos(media_dados)

        return True

    except Exception as e:
        print(f"⚠️ Erro ao enviar dados periódicos: {e}")
        return False


# ================================
# ⏱️ Scheduler alinhado no relógio
# ================================
_timer_envio = None
_INTERVALO_MIN = 5  # intervalo fixo de 5 minutos


def _proximo_disparo():
    """
    Calcula o próximo múltiplo de 5 minutos no relógio.
    Exemplo: 10:02 → 10:05, 10:07 → 10:10.
    """
    agora = datetime.now().replace(second=0, microsecond=0)
    minuto = (agora.minute // _INTERVALO_MIN) * _INTERVALO_MIN
    base = agora.replace(minute=minuto)
    alvo = base + timedelta(minutes=_INTERVALO_MIN)
    return alvo


def _tick_envio(estufa_id):
    """
    Função disparada pelo Timer.
    Tenta enviar os dados e agenda o próximo disparo.
    """
    try:
        enviar_dados_periodicamente(estufa_id, mostrar_no_terminal=True)
    finally:
        _agendar_envio(estufa_id)


def _agendar_envio(estufa_id):
    """
    Agenda o próximo envio cravado no relógio.
    """
    global _timer_envio
    if _timer_envio:
        _timer_envio.cancel()

    alvo = _proximo_disparo()
    delay = (alvo - datetime.now()).total_seconds()
    delay = max(1.0, delay)  # segurança

    _timer_envio = threading.Timer(delay, _tick_envio, args=(estufa_id,))
    _timer_envio.daemon = True
    _timer_envio.start()


def iniciar_envio_periodico(estufa_id):
    """
    Inicia o envio automático de dados,
    rodando sempre em múltiplos de 5 minutos (00, 05, 10...).
    """
    _agendar_envio(estufa_id)


def parar_envio_periodico():
    """
    Interrompe o envio periódico.
    """
    global _timer_envio
    if _timer_envio:
        _timer_envio.cancel()
        _timer_envio = None

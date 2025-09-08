"""
main.py — Ponto de entrada do backend da estufa inteligente.

Responsabilidades:
- Inicializa sensores e atuadores conectados ao Raspberry Pi.
- Executa o ciclo principal da estufa (coleta, controle, envio de dados).
- Inicia o logger de dados em CSV (teste_logger).
- Ativa listeners do Firestore para iniciar, reiniciar e avançar fases.
- Mantém o processo ativo continuamente, mesmo se rodando em background.
- Trata interrupções (CTRL+C) para desligar atuadores.
"""

import threading
import board
import signal
import sys
import time

# ===============================
# Sensores
# ===============================
from modules.sensores.luminosidade import BH1750
from modules.sensores.temperatura_ar_umidade_ar import DHT22
from modules.sensores.temperatura_solo import DS18B20
from modules.sensores.umidade_solo import UmidadeSolo

# ===============================
# Atuadores
# ===============================
from modules.atuadores.aquecedor import Aquecedor
from modules.atuadores.luminaria import Luminaria
from modules.atuadores.bomba import Bomba
from modules.atuadores.ventoinha import Ventoinha

# ===============================
# Configuração
# ===============================
from config.configuracao_local import carregar_configuracao_local

# ===============================
# Services
# ===============================
from services.ciclo_service import ciclo_estufa
from services.listeners_service import (
    escutar_solicitacao_iniciar,
    escutar_solicitacao_reiniciar,
    escutar_solicitacao_avancar,
)

# ===============================
# Testes
# ===============================
from testes.teste_logger import teste_logger


# 🔥 Identificador único da estufa
ESTUFA_ID = "EG001"

# Carrega configuração inicial
config = carregar_configuracao_local(ESTUFA_ID)
if not config:
    exit("❌ Erro ao carregar a configuração da estufa.")

# 🔥 Intervalo do ciclo principal (segundos)
TEMPO_CICLO = 30

# ===============================
# Inicialização de Sensores
# ===============================
luminosidade_sensor = BH1750()
temperatura_solo_sensor = DS18B20()
temperatura_ar_sensor = DHT22(pin=board.D17)  # GPIO 17
umidade_solo_sensor = UmidadeSolo()

# ===============================
# Inicialização de Atuadores
# ===============================
ventoinha = Ventoinha()
luminaria = Luminaria()
bomba = Bomba()
aquecedor = Aquecedor()


def encerrar(sig, frame):
    """Tratamento de CTRL+C → desliga atuadores, atualiza Firebase e limpa sensores."""
    print("\n⛔ Encerrando sistema de forma segura...")

    try:
        # Desliga atuadores fisicamente
        aquecedor.desligar()
        ventoinha.desligar()
        luminaria.desligar()
        bomba.desligar()

        print("✅ Atuadores desligados.")
    except Exception as e:
        print(f"⚠️ Erro ao desligar atuadores: {e}")

    sys.exit(0)


if __name__ == "__main__":
    # Registra handler para CTRL+C
    signal.signal(signal.SIGINT, encerrar)

    # 🌱 Thread do ciclo principal
    thread_ciclo = threading.Thread(
        target=ciclo_estufa,
        args=(
            ESTUFA_ID,
            luminosidade_sensor,
            temperatura_solo_sensor,
            temperatura_ar_sensor,
            umidade_solo_sensor,
            ventoinha,
            luminaria,
            bomba,
            aquecedor,
            TEMPO_CICLO,
        ),
        daemon=True,
    )

    # 📝 Thread do logger CSV
    thread_logger = threading.Thread(target=teste_logger, daemon=True)

    # Inicia threads principais
    thread_ciclo.start()
    thread_logger.start()

    # Ativa listeners do Firestore (rodam em background sem threads extras)
    escutar_solicitacao_iniciar(ESTUFA_ID)
    escutar_solicitacao_reiniciar(ESTUFA_ID)
    escutar_solicitacao_avancar(ESTUFA_ID)

    # Mantém processo vivo
    thread_ciclo.join()
    thread_logger.join()

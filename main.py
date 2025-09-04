import threading
import board

# Sensores
from Modules.SENSORES.BH1750 import BH1750
from Modules.SENSORES.DHT22 import DHT22
from Modules.SENSORES.DS18B20 import DS18B20
from Modules.SENSORES.UMIDADE_SOLO import UmidadeSolo

# Atuadores
from Modules.ATUADORES.Aquecedor import Aquecedor
from Modules.ATUADORES.Luminaria import Luminaria
from Modules.ATUADORES.Bomba import Bomba
from Modules.ATUADORES.Ventoinha import Ventoinha

# Configuração
from Config.configuracao_local import carregar_configuracao_local

# Services
from Services.ciclo_estufa_service import ciclo_estufa
from Services.listeners_service import (
    escutar_solicitacao_iniciar,
    escutar_solicitacao_reiniciar,
    escutar_solicitacao_avancar,
)


# Teste da estufa
from Testes.teste_logger import teste_logger


# 🔥 Identificador da estufa
estufa_id = "EG001"
config = carregar_configuracao_local(estufa_id)
if not config:
    exit("Erro ao carregar a configuração da estufa.")

# 🔥 Tempo do ciclo de leitura
tempo_ciclo = 30

# 🔥 Inicializa os sensores
luminosidade_sensor = BH1750()
temperatura_solo_sensor = DS18B20()
temperatura_ar_sensor = DHT22()
umidade_solo_sensor = UmidadeSolo()

# 🔥 Inicializa os atuadores
ventoinha = Ventoinha()
luminaria = Luminaria()
bomba = Bomba()
aquecedor = Aquecedor()

if __name__ == "__main__":
    threads = [
        # 🌱 Ciclo unificado
        threading.Thread(
            target=ciclo_estufa,
            args=(
                estufa_id,
                luminosidade_sensor,
                temperatura_solo_sensor,
                temperatura_ar_sensor,
                umidade_solo_sensor,
                ventoinha,
                luminaria,
                bomba,
                aquecedor,
                tempo_ciclo,
            ),
        ),
        # 🎧 Listeners em paralelo
        threading.Thread(target=escutar_solicitacao_iniciar, args=(estufa_id,)),
        threading.Thread(target=escutar_solicitacao_reiniciar, args=(estufa_id,)),
        threading.Thread(target=escutar_solicitacao_avancar, args=(estufa_id,)),
    ]

    # 🔎 Teste Estufa
    thread_logger = threading.Thread(target=teste_logger)

    # Inicia todas as threads
    for t in threads:
        t.start()

    thread_logger.start()

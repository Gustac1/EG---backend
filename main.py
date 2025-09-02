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
from Services.coleta_service import coletar_dados
from Services.envio_service import enviar_dados_periodicamente
from Services.controle_service import controlar_atuadores
from Services.listeners_service import (
    escutar_alteracoes_configuracao,
    escutar_overrides_desejados,
    escutar_solicitacao_iniciar,
    escutar_solicitacao_reiniciar,
    escutar_solicitacao_avancar
)
from Services.fase_service import (
    monitorar_avanco_fase,
    exibir_status_fase
)

# Utils (exibição no terminal)
from Utils.display import (
    exibir_bloco_sensores,
    exibir_dados_periodicos,
    exibir_status_atuadores
)

# 🔥 Identificador da estufa
estufa_id = "EG001"
config = carregar_configuracao_local(estufa_id)
if not config:
    exit("❌ Erro ao carregar a configuração da estufa.")

# 🔥 Inicializa os sensores
luminosidade_sensor = BH1750()
temperatura_solo_sensor = DS18B20()
temperatura_ar_sensor = DHT22(pin=board.D17)
umidade_solo_sensor = UmidadeSolo()

# 🔥 Inicializa os atuadores
ventoinha = Ventoinha()
luminaria = Luminaria()
bomba = Bomba()
aquecedor = Aquecedor()

if __name__ == "__main__":
    # Threads principais
    threads = [
        threading.Thread(
            target=coletar_dados,
            args=(estufa_id,
                  luminosidade_sensor,
                  temperatura_solo_sensor,
                  temperatura_ar_sensor,
                  umidade_solo_sensor,
                  exibir_bloco_sensores)
        ),
        threading.Thread(
            target=enviar_dados_periodicamente,
            args=(estufa_id, exibir_dados_periodicos)
        ),
        threading.Thread(
            target=controlar_atuadores,
            args=(estufa_id,
                  ventoinha, luminaria, bomba, aquecedor,
                  temperatura_ar_sensor, umidade_solo_sensor,
                  exibir_status_atuadores, exibir_status_fase)
        ),
        threading.Thread(target=escutar_alteracoes_configuracao, args=(estufa_id,)),
        threading.Thread(target=escutar_overrides_desejados, args=(estufa_id,)),


        threading.Thread(
            target=escutar_solicitacao_iniciar,
            args=(estufa_id,
            ventoinha, luminaria, bomba, aquecedor,
            temperatura_ar_sensor, umidade_solo_sensor,
            exibir_status_atuadores, exibir_status_fase)
        ),  

        threading.Thread(
            target=escutar_solicitacao_reiniciar,
            args=(estufa_id,
                  ventoinha, luminaria, bomba, aquecedor,
                  exibir_status_atuadores, exibir_status_fase)
        ), 
        

        threading.Thread(target=escutar_solicitacao_avancar, args=(estufa_id,)),
        threading.Thread(target=monitorar_avanco_fase, args=(estufa_id,))
    ]

    # Inicia todas as threads
    for t in threads:
        t.start()
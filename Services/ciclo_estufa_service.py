# Services/ciclo_estufa_service.py
import time
from contextlib import nullcontext
from Utils.logger import warn
from Services.controle_service import controlar_atuadores
from Services.envio_service import enviar_dados_periodicamente
from Services.fase_service import verificar_e_avancar_fase
from Services.coleta_service import coletar_dados
from Config.firebase_config import enviar_dados_realtime
from Services.fase_service import exibir_status_fase
from Utils.display import (
    exibir_bloco_sensores,
    exibir_status_atuadores,
    exibir_dados_periodicos,
)
from Config.configuracao_local import carregar_configuracao_local
from Config.firebase_config import atualizar_status_atuador


def ciclo_estufa(
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
):
    while True:
        try:
            # 1. Carrega Configs
            config = carregar_configuracao_local(estufa_id)

            # 1. Coleta sensores
            dados = coletar_dados(
                luminosidade_sensor,
                temperatura_solo_sensor,
                temperatura_ar_sensor,
                umidade_solo_sensor,
            )

            # 2. Controle atuadores
            status_atuadores = controlar_atuadores(
                ventoinha,
                luminaria,
                bomba,
                aquecedor,
                dados.get("TemperaturaDoArAtual"),
                dados.get("UmidadeDoArAtual"),
                dados.get("UmidadeDoSoloAtual"),
                config,
            )
            if status_atuadores:
                for nome, (ativo, motivo) in status_atuadores.items():
                    atualizar_status_atuador(estufa_id, nome, ativo, motivo)

            exibir_status_fase(config)
            exibir_status_atuadores(status_atuadores)

            if dados:
                enviar_dados_realtime(estufa_id, dados)

            if dados and exibir_bloco_sensores:
                exibir_bloco_sensores(dados)

            # 3. Envio periódico de médias
            enviar_dados_periodicamente(estufa_id, exibir_dados_periodicos)

            # 4. Verifica avanço de fase
            nova_fase = verificar_e_avancar_fase(estufa_id, config)
            if nova_fase:
                print(f"Estufa {estufa_id} avançou para a fase {nova_fase}")

            # 5. Log de ciclo concluído
            print(f"🔄 Ciclo da estufa concluído às {time.strftime('%H:%M:%S')}")

        except Exception as e:
            warn(f"⚠️ Erro no ciclo_estufa: {e}")

        # 6. Intervalo único do ciclo
        print(f"⏳ Aguardando próximo ciclo ({tempo_ciclo}s)...\n")
        time.sleep(tempo_ciclo)

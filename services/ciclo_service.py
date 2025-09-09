# services/ciclo_service.py
import time
import threading
from services.controle_service import controlar_atuadores
from services.envio_service import enviar_dados_periodicamente
from services.fases_service import verificar_e_avancar_fase
from services.coleta_service import coletar_dados
from config.firebase_config import enviar_dados_realtime, atualizar_status_atuador
from config.configuracao_local import carregar_configuracao_local
from utils.display import (
    exibir_bloco_sensores,
    exibir_status_atuadores,
    exibir_dados_periodicos,
    exibir_status_fase,
    limpar_terminal,
)

# Evento global usado para resetar o ciclo de forma imediata
ciclo_reset_event = threading.Event()


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
    """
    Executa o ciclo principal da estufa.

    Fluxo:
      1. Limpa terminal e carrega configuração ativa da estufa.
      2. Coleta leituras dos sensores.
      3. Controla atuadores com base nas leituras e configuração.
      4. Atualiza status dos atuadores no Firestore.
      5. Envia dados atuais para o Realtime Database.
      6. Exibe status de sensores, atuadores e fase no terminal.
      7. Calcula e envia médias periódicas para o Firestore.
      8. Verifica se a fase deve avançar automaticamente.
      9. Aguarda até o próximo ciclo (ou reseta imediatamente se solicitado).

    Parâmetros:
        estufa_id (str): Identificador único da estufa (ex.: "EG001").
        luminosidade_sensor (obj): Instância do sensor BH1750.
        temperatura_solo_sensor (obj): Instância do sensor DS18B20.
        temperatura_ar_sensor (obj): Instância do sensor DHT22.
        umidade_solo_sensor (obj): Instância do sensor de umidade do solo.
        ventoinha (obj): Atuador da ventoinha.
        luminaria (obj): Atuador da luminária.
        bomba (obj): Atuador da bomba de irrigação.
        aquecedor (obj): Atuador do aquecedor.
        tempo_ciclo (int): Intervalo entre ciclos, em segundos.

    Retorna:
        None (loop infinito até interrupção externa).
    """
    while True:
        try:
            # 1. Limpa tela e carrega configuração atual
            # limpar_terminal()
            config = carregar_configuracao_local(estufa_id)

            # 2. Coleta sensores
            dados = coletar_dados(
                luminosidade_sensor,
                temperatura_solo_sensor,
                temperatura_ar_sensor,
                umidade_solo_sensor,
            )

            # 3. Controle dos atuadores
            status_atuadores = controlar_atuadores(
                ventoinha,
                luminaria,
                bomba,
                aquecedor,
                dados.get("TemperaturaDoArAtual") if dados else None,
                dados.get("UmidadeDoArAtual") if dados else None,
                dados.get("UmidadeDoSoloAtual") if dados else None,
                config,
            )
            if status_atuadores:
                for nome, (ativo, motivo) in status_atuadores.items():
                    atualizar_status_atuador(estufa_id, nome, ativo, motivo)

            # 4. Exibição no terminal
            exibir_status_fase(config)
            exibir_status_atuadores(status_atuadores)
            if dados:
                enviar_dados_realtime(estufa_id, dados)
                exibir_bloco_sensores(dados)

            # 5. Envio periódico de médias
            enviar_dados_periodicamente(estufa_id, exibir_dados_periodicos)

            # 6. Verifica avanço de fase
            nova_fase = verificar_e_avancar_fase(estufa_id, config)
            if nova_fase:
                print(f"⏩ Estufa {estufa_id} avançou para a fase {nova_fase}")

            # 7. Conclusão do ciclo
            print(f"✅ Ciclo da estufa concluído às {time.strftime('%H:%M:%S')}")

        except Exception as e:
            print(f"⚠️ Erro no ciclo_estufa: {e}")

        # 8. Intervalo até o próximo ciclo (com suporte a reset imediato)
        print(f"⏳ Aguardando próximo ciclo ({tempo_ciclo}s)...\n")
        if ciclo_reset_event.wait(timeout=tempo_ciclo):
            print("🔄 Ciclo resetado por listener!")
            ciclo_reset_event.clear()

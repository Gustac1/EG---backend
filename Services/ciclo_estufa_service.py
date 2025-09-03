# Services/ciclo_estufa_service.py
import time
from Utils.logger import warn
from Config.firebase_config import (
    enviar_dados_realtime,
    enviar_dados_firestore,
    atualizar_status_atuador,
    atualizar_status_ventilacao,
    realtime_db
)
from Config.configuracao_local import carregar_configuracao_local

# Buffer para histórico (mantém compatibilidade com envio periódico)
buffer_sensores = {
    "Luminosidade": [],
    "TemperaturaDoSolo": [],
    "Temperatura": [],
    "Umidade": [],
    "UmidadeDoSolo": []
}

def ciclo_estufa(estufa_id,
                 luminosidade_sensor,
                 temperatura_solo_sensor,
                 temperatura_ar_sensor,
                 umidade_solo_sensor,
                 ventoinha,
                 luminaria,
                 bomba,
                 aquecedor,
                 intervalo=30,
                 exibir_bloco_sensores=None,
                 exibir_status_atuadores=None,
                 exibir_status_fase=None):
    """
    Loop unificado da estufa:
    - Lê sensores
    - Calcula atuadores
    - Atualiza Firebase (Realtime + Firestore)
    - Mantém buffer para envio periódico
    - (Opcional) exibe dados no terminal
    """

    while True:
        try:
            # --- Carrega config ---
            config = carregar_configuracao_local(estufa_id)
            if not config:
                warn("⚠️ Erro ao carregar configuração local.")
                time.sleep(intervalo)
                continue

            # --- Caso Standby ---
            if config.get("FaseAtual") == "Standby":
                motivo = "Estufa em Standby"
                ventoinha.desligar(); atualizar_status_ventilacao(estufa_id, False)
                luminaria.desligar(); bomba.desligar(); aquecedor.desligar()

                status_atuadores = {
                    "Aquecedor": (False, motivo),
                    "Ventoinha": (False, motivo),
                    "Luminária": (False, motivo),
                    "Bomba":     (False, motivo)
                }

                if exibir_status_atuadores: exibir_status_atuadores(status_atuadores)
                atualizar_status_atuador(estufa_id, "Aquecedor", False, motivo)
                atualizar_status_atuador(estufa_id, "Ventilacao", False, motivo)
                atualizar_status_atuador(estufa_id, "Luminaria", False, motivo)
                atualizar_status_atuador(estufa_id, "Bomba", False, motivo)
                if exibir_status_fase: exibir_status_fase(config)
                time.sleep(intervalo); continue

            # --- Caso Colheita ou sistema parado ---
            if config.get("FaseAtual") == "Colheita" or not config.get("EstadoSistema", False):
                motivo = "🌾 Fase Colheita" if config.get("FaseAtual") == "Colheita" else "⛔ Sistema desativado"
                ventoinha.desligar(); atualizar_status_ventilacao(estufa_id, False)
                luminaria.desligar(); bomba.desligar(); aquecedor.desligar()

                status_atuadores = {
                    "Aquecedor": (False, motivo),
                    "Ventoinha": (False, motivo),
                    "Luminária": (False, motivo),
                    "Bomba":     (False, motivo)
                }

                if exibir_status_atuadores: exibir_status_atuadores(status_atuadores)
                if exibir_status_fase: exibir_status_fase(config)
                time.sleep(intervalo); continue

            # --- 1. Leitura dos sensores ---
            lux = luminosidade_sensor.ler_luminosidade()
            temp_solo = temperatura_solo_sensor.read_temp()
            temp_ar, umi_ar = temperatura_ar_sensor.ler_dados()
            umi_solo = umidade_solo_sensor.ler_umidade()

            # Arredondamentos
            lux = round(lux, 2) if lux is not None else None
            temp_solo = round(temp_solo, 2) if temp_solo is not None else None
            temp_ar = round(temp_ar, 2) if temp_ar is not None else None
            umi_ar = round(umi_ar, 2) if umi_ar is not None else None
            umi_solo = round(umi_solo, 2) if umi_solo is not None else None

            sensores = {
                "LuminosidadeAtual": lux,
                "TemperaturaDoArAtual": temp_ar,
                "UmidadeDoArAtual": umi_ar,
                "TemperaturaDoSoloAtual": temp_solo,
                "UmidadeDoSoloAtual": umi_solo,
                "timestamp": round(time.time(), 2)
            }

            # Buffer histórico
            if lux is not None: buffer_sensores["Luminosidade"].append(lux)
            if temp_solo is not None: buffer_sensores["TemperaturaDoSolo"].append(temp_solo)
            if temp_ar is not None: buffer_sensores["Temperatura"].append(temp_ar)
            if umi_ar is not None: buffer_sensores["Umidade"].append(umi_ar)
            if umi_solo is not None: buffer_sensores["UmidadeDoSolo"].append(umi_solo)

            # --- 2. Controle dos atuadores ---
            aquecedor_ativo, motivo_aquecedor = aquecedor.controlar(temp_ar, config)
            ventoinha_ativa, motivo_ventoinha = ventoinha.controlar(temp_ar, umi_ar, aquecedor_ativo, config)
            luminaria_ativa, motivo_luminaria = luminaria.controlar(config)
            bomba_ativa, motivo_bomba = bomba.controlar(umi_solo, config)

            status_atuadores = {
                "Aquecedor": (aquecedor_ativo, motivo_aquecedor),
                "Ventoinha": (ventoinha_ativa, motivo_ventoinha),
                "Luminária": (luminaria_ativa, motivo_luminaria),
                "Bomba":     (bomba_ativa, motivo_bomba)
            }

            # --- 3. Envio sincronizado ---
            # Sensores → Realtime
            enviar_dados_realtime(estufa_id, sensores)
            # Histórico → Firestore
            enviar_dados_firestore(estufa_id, sensores)
            # Atuadores → Firestore
            atualizar_status_atuador(estufa_id, "Aquecedor", aquecedor_ativo, motivo_aquecedor)
            atualizar_status_atuador(estufa_id, "Ventilacao", ventoinha_ativa, motivo_ventoinha)
            atualizar_status_atuador(estufa_id, "Luminaria", luminaria_ativa, motivo_luminaria)
            atualizar_status_atuador(estufa_id, "Bomba", bomba_ativa, motivo_bomba)

            # Opcional: salvar PainelAtual junto
            painel_atual = {
                "timestamp": sensores["timestamp"],
                "sensores": sensores,
                "atuadores": {
                    "Aquecedor": {"Estado": aquecedor_ativo, "Motivo": motivo_aquecedor},
                    "Ventoinha": {"Estado": ventoinha_ativa, "Motivo": motivo_ventoinha},
                    "Luminaria": {"Estado": luminaria_ativa, "Motivo": motivo_luminaria},
                    "Bomba": {"Estado": bomba_ativa, "Motivo": motivo_bomba},
                }
            }
            realtime_db.child(f"Dispositivos/{estufa_id}/PainelAtual").set(painel_atual)

            # --- 4. Exibição no terminal ---
            if exibir_bloco_sensores: exibir_bloco_sensores(sensores)
            if exibir_status_atuadores: exibir_status_atuadores(status_atuadores)
            if exibir_status_fase: exibir_status_fase(config)

        except Exception as e:
            warn(f"⚠️ Erro no ciclo_estufa: {e}")

        time.sleep(intervalo)

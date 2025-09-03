# Services/controle_service.py
import time
from Utils.logger import warn
from Config.firebase_config import atualizar_status_atuador, atualizar_status_ventilacao
from Config.configuracao_local import carregar_configuracao_local

def controlar_atuadores(estufa_id, ventoinha, luminaria, bomba, aquecedor,
                        temperatura_ar_sensor, umidade_solo_sensor,
                        exibir_status_atuadores=None, exibir_status_fase=None):
    """
    Controla os atuadores com base na configuração e leituras atuais.
    Mantém a mesma assinatura do main (passando cada atuador/sensor separado).
    """
    while True:
        try:
            config = carregar_configuracao_local(estufa_id)
            if not config:
                print("⚠️ Erro ao carregar configuração local.")
                time.sleep(30)
                continue

            # --- Standby ---
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
                time.sleep(30); continue

            # --- Colheita ou sistema parado ---
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
                if exibir_status_fase: exibir_status_fase(config)
                if exibir_status_atuadores: exibir_status_atuadores(status_atuadores)
                time.sleep(30); continue

            # --- Coleta para decisão ---
            temperatura_ar, umidade_ar = temperatura_ar_sensor.ler_dados()
            umidade_solo = umidade_solo_sensor.ler_umidade()

            # --- Aquecedor ---
            aquecedor_ativo, motivo_aquecedor = aquecedor.controlar(
                temperatura_ar=temperatura_ar, config=config
            )
            atualizar_status_atuador(estufa_id, "Aquecedor", aquecedor_ativo, motivo_aquecedor)

            # --- Ventoinha ---
            ventoinha_ativa, motivo_ventoinha = ventoinha.controlar(
                temperatura_ar=temperatura_ar,
                umidade_ar=umidade_ar,
                aquecedor_ativo=aquecedor_ativo,
                config=config
            )
            atualizar_status_ventilacao(estufa_id, ventoinha_ativa)
            atualizar_status_atuador(estufa_id, "Ventilacao", ventoinha_ativa, motivo_ventoinha)

            # --- Luminária ---
            luminaria_ativa, motivo_luminaria = luminaria.controlar(config=config)
            atualizar_status_atuador(estufa_id, "Luminaria", luminaria_ativa, motivo_luminaria)

            # --- Bomba ---
            bomba_ativa, motivo_bomba = bomba.controlar(umidade_solo=umidade_solo, config=config)
            atualizar_status_atuador(estufa_id, "Bomba", bomba_ativa, motivo_bomba)

            # --- Exibição no terminal ---
            status_atuadores = {
                "Aquecedor": (aquecedor_ativo, motivo_aquecedor),
                "Ventoinha": (ventoinha_ativa, motivo_ventoinha),
                "Luminária": (luminaria_ativa, motivo_luminaria),
                "Bomba":     (bomba_ativa, motivo_bomba)
            }
            if exibir_status_atuadores: exibir_status_atuadores(status_atuadores)
            if exibir_status_fase: exibir_status_fase(config)

        except Exception as e:
            warn(f"Erro ao controlar atuadores: {e}")

        time.sleep(30)


def rodar_controle_once(estufa_id, ventoinha, luminaria, bomba, aquecedor,
                        temperatura_ar_sensor, umidade_solo_sensor,
                        exibir_status_atuadores=None, exibir_status_fase=None):
    """Executa uma rodada única do controle de atuadores (sem loop infinito)."""
    try:
        config = carregar_configuracao_local(estufa_id)
        if not config:
            warn("⚠️ Erro ao carregar configuração local.")
            return

        temperatura_ar, umidade_ar = temperatura_ar_sensor.ler_dados()
        umidade_solo = umidade_solo_sensor.ler_umidade()

        # --- Aquecedor ---
        aquecedor_ativo, motivo_aquecedor = aquecedor.controlar(temperatura_ar, config)
        atualizar_status_atuador(estufa_id, "Aquecedor", aquecedor_ativo, motivo_aquecedor)

        # --- Ventoinha ---
        ventoinha_ativa, motivo_ventoinha = ventoinha.controlar(
            temperatura_ar, umidade_ar, aquecedor_ativo, config
        )
        atualizar_status_ventilacao(estufa_id, ventoinha_ativa)
        atualizar_status_atuador(estufa_id, "Ventilacao", ventoinha_ativa, motivo_ventoinha)

        # --- Luminária ---
        luminaria_ativa, motivo_luminaria = luminaria.controlar(config=config)
        atualizar_status_atuador(estufa_id, "Luminaria", luminaria_ativa, motivo_luminaria)

        # --- Bomba ---
        bomba_ativa, motivo_bomba = bomba.controlar(umidade_solo, config)
        atualizar_status_atuador(estufa_id, "Bomba", bomba_ativa, motivo_bomba)

        # --- Exibição no terminal ---
        status_atuadores = {
            "Aquecedor": (aquecedor_ativo, motivo_aquecedor),
            "Ventoinha": (ventoinha_ativa, motivo_ventoinha),
            "Luminária": (luminaria_ativa, motivo_luminaria),
            "Bomba":     (bomba_ativa, motivo_bomba)
        }
        if exibir_status_atuadores:
            exibir_status_atuadores(status_atuadores)
        if exibir_status_fase:
            exibir_status_fase(config)

    except Exception as e:
        warn(f"Erro em rodada única de controle: {e}")


def desligar_todos_atuadores(estufa_id, ventoinha, luminaria, bomba, aquecedor,
                             exibir_status_atuadores=None, exibir_status_fase=None):
    """
    Desliga imediatamente todos os atuadores e atualiza o status no Firestore.
    Usado em eventos de reinício/reset.
    """
    try:
        motivo = "Estufa em Standby"

        ventoinha.desligar(); atualizar_status_ventilacao(estufa_id, False)
        luminaria.desligar(); bomba.desligar(); aquecedor.desligar()

        status_atuadores = {
            "Aquecedor": (False, motivo),
            "Ventoinha": (False, motivo),
            "Luminária": (False, motivo),
            "Bomba":     (False, motivo)
        }

        atualizar_status_atuador(estufa_id, "Aquecedor", False, motivo)
        atualizar_status_atuador(estufa_id, "Ventilacao", False, motivo)
        atualizar_status_atuador(estufa_id, "Luminaria", False, motivo)
        atualizar_status_atuador(estufa_id, "Bomba", False, motivo)

        if exibir_status_atuadores:
            exibir_status_atuadores(status_atuadores)

        # carrega a config atualizada em standby e mostra no terminal
        from Config.configuracao_local import carregar_configuracao_local
        config = carregar_configuracao_local(estufa_id)
        if exibir_status_fase and config:
            exibir_status_fase(config)

    except Exception as e:
        warn(f"Erro ao desligar atuadores no reinício: {e}")
       
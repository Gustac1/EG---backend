import time
from Utils.logger import warn
from Config.firebase_config import enviar_dados_realtime

# Buffer para o histórico (compartilhado com envio periódico)
buffer_sensores = {
    "Luminosidade": [],
    "TemperaturaDoSolo": [],
    "Temperatura": [],
    "Umidade": [],
    "UmidadeDoSolo": []
}

def coletar_dados(estufa_id,
                  luminosidade_sensor,
                  temperatura_solo_sensor,
                  temperatura_ar_sensor,
                  umidade_solo_sensor,
                  exibir_bloco_sensores=None):
    """
    Coleta os dados dos sensores e envia valores atuais para o Realtime Database.
    Mantém a mesma assinatura do main original (sensores separados).
    """
    while True:
        try:
            lux = luminosidade_sensor.ler_luminosidade()
            temperatura_solo = temperatura_solo_sensor.read_temp()
            temperatura_ar, umidade_ar = temperatura_ar_sensor.ler_dados()
            umidade_solo = umidade_solo_sensor.ler_umidade()

            # Arredondamentos
            lux = round(lux, 2) if lux is not None else None
            temperatura_solo = round(temperatura_solo, 2) if temperatura_solo is not None else None
            temperatura_ar = round(temperatura_ar, 2) if temperatura_ar is not None else None
            umidade_ar = round(umidade_ar, 2) if umidade_ar is not None else None
            umidade_solo = round(umidade_solo, 2) if umidade_solo is not None else None

            dados_atuais = {
                "LuminosidadeAtual": lux,
                "TemperaturaDoArAtual": temperatura_ar,
                "UmidadeDoArAtual": umidade_ar,
                "TemperaturaDoSoloAtual": temperatura_solo,
                "UmidadeDoSoloAtual": umidade_solo,
                "timestamp": round(time.time(), 2)
            }

            if enviar_dados_realtime(estufa_id, dados_atuais):
                if exibir_bloco_sensores:
                    exibir_bloco_sensores(dados_atuais)

            # Buffer histórico
            if lux is not None: buffer_sensores["Luminosidade"].append(lux)
            if temperatura_solo is not None: buffer_sensores["TemperaturaDoSolo"].append(temperatura_solo)
            if temperatura_ar is not None: buffer_sensores["Temperatura"].append(temperatura_ar)
            if umidade_ar is not None: buffer_sensores["Umidade"].append(umidade_ar)
            if umidade_solo is not None: buffer_sensores["UmidadeDoSolo"].append(umidade_solo)

        except Exception as e:
            warn(f"Erro ao coletar dados dos sensores: {e}")

        time.sleep(30)

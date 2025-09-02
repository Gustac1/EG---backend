# Services/envio_service.py
import time
from Utils.logger import warn
from Config.firebase_config import enviar_dados_firestore
from Services.coleta_service import buffer_sensores  # reaproveita o mesmo buffer

def enviar_dados_periodicamente(estufa_id, exibir_dados_periodicos=None):
    """
    A cada 5 minutos, calcula a média dos sensores e envia para o Firestore.
    Mantém a mesma assinatura do main original.
    """
    while True:
        try:
            if len(buffer_sensores["Luminosidade"]) >= 5:
                media_dados = {
                    "Luminosidade": sum(buffer_sensores["Luminosidade"]) / len(buffer_sensores["Luminosidade"]),
                    "TemperaturaDoSolo": sum(buffer_sensores["TemperaturaDoSolo"]) / len(buffer_sensores["TemperaturaDoSolo"]),
                    "Temperatura": sum(buffer_sensores["Temperatura"]) / len(buffer_sensores["Temperatura"]),
                    "Umidade": sum(buffer_sensores["Umidade"]) / len(buffer_sensores["Umidade"]),
                    "UmidadeDoSolo": sum(buffer_sensores["UmidadeDoSolo"]) / len(buffer_sensores["UmidadeDoSolo"]),
                    "timestamp": round(time.time(), 2)
                }

                # 🔥 Limpa buffers
                for key in buffer_sensores:
                    buffer_sensores[key].clear()

                # 🔥 Envia ao Firestore
                enviar_dados_firestore(estufa_id, media_dados)

                if exibir_dados_periodicos:
                    exibir_dados_periodicos(media_dados)

        except Exception as e:
            warn(f"Erro ao enviar dados para o Firestore: {e}")

        time.sleep(300)  # 5 minutos

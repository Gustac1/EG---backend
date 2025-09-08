# services/envio_service.py
import time
from config.firebase_config import enviar_dados_firestore
from services.coleta_service import buffer_sensores  # reaproveita o mesmo buffer


def media(lista):
    """
    Calcula a média de uma lista.

    Parâmetros:
        lista (list[float]): lista de valores numéricos.

    Retorna:
        float | None:
            - Média dos valores, se a lista não estiver vazia.
            - None, se a lista estiver vazia.
    """
    return sum(lista) / len(lista) if lista else None


def enviar_dados_periodicamente(estufa_id, exibir_dados_periodicos=None):
    """
    Executa uma rodada única de envio de médias dos sensores.

    Fluxo:
        1. Verifica se há dados suficientes no buffer (>= 5 leituras de Luminosidade).
        2. Calcula a média de cada sensor.
        3. Limpa os buffers após o envio.
        4. Envia as médias para o Firestore (histórico).
        5. Opcionalmente exibe as médias no terminal.

    Critério de envio:
        - É necessário pelo menos 5 valores de Luminosidade acumulados.
        - As demais variáveis podem ter menos leituras:
            - Se houver dados → média calculada.
            - Se não houver → retorna None.

    Parâmetros:
        estufa_id (str): Identificador único da estufa.
        exibir_dados_periodicos (callable|None): função opcional para exibir no terminal.

    Retorna:
        None, em execução normal.
        dict com valores None, em caso de erro.
    """
    try:
        # critério de disparo → 5 valores de Luminosidade
        if len(buffer_sensores["Luminosidade"]) >= 5:
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

            # 🖥️ Exibe no terminal (se função passada)
            if exibir_dados_periodicos:
                exibir_dados_periodicos(media_dados)

    except Exception as e:
        print(f"⚠️ Erro ao enviar dados periódicos: {e}")
        return {
            "Luminosidade": None,
            "TemperaturaDoSolo": None,
            "Temperatura": None,
            "Umidade": None,
            "UmidadeDoSolo": None,
            "timestamp": round(time.time(), 2),
        }

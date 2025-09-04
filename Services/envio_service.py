import time
from Config.firebase_config import enviar_dados_firestore
from Services.coleta_service import buffer_sensores  # reaproveita o mesmo buffer


def media(lista):
    """Calcula a média de uma lista ou retorna None se estiver vazia."""
    return sum(lista) / len(lista) if lista else None


def enviar_dados_periodicamente(estufa_id, exibir_dados_periodicos=None):
    """
    Executa uma rodada única de envio de médias dos sensores:
      - Se houver dados suficientes no buffer, calcula as médias.
      - Envia o resultado ao Firestore.
      - Limpa os buffers após o envio.
      - Não retorna nada (exceto em caso de erro, retorna todos None).

    Critério de envio:
      - Pelo menos 5 valores de Luminosidade acumulados (proxy de tempo decorrido).
      - As outras variáveis podem ter menos leituras, mas se estiverem vazias retornam None.

    Parâmetros:
        estufa_id (str): Identificador único da estufa.
        exibir_dados_periodicos (callable|None): função opcional para exibir no terminal.
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

            # 🔥 Limpa buffers
            for key in buffer_sensores:
                buffer_sensores[key].clear()

            # 🔥 Envia ao Firestore
            enviar_dados_firestore(estufa_id, media_dados)

            if exibir_dados_periodicos:
                exibir_dados_periodicos(media_dados)

    except Exception as e:
        print(f"[ERRO] Falha ao enviar dados periódicos: {e}")
        return {
            "Luminosidade": None,
            "TemperaturaDoSolo": None,
            "Temperatura": None,
            "Umidade": None,
            "UmidadeDoSolo": None,
            "timestamp": round(time.time(), 2),
        }

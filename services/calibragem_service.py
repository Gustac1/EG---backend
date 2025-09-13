import threading
import time
from config.firebase.realtime_utils import enviar_dados_realtime

# Flags globais
calibragem_luminosidade_ativa = False
_thread_calibragem = None


def arredondar(valor, casas=2):
    """
    Arredonda um valor numérico para o número de casas decimais especificado.

    Parâmetros:
        valor (float|None): número a ser arredondado.
        casas (int): número de casas decimais (default=2).

    Retorna:
        - Valor arredondado (float) se for numérico.
        - None, se o valor original for None.

    Exemplos:
        arredondar(25.6789) → 25.68
        arredondar(None)    → None
    """
    return round(valor, casas) if valor is not None else None


def iniciar_calibragem_luminosidade(sensor, estufa_id):
    """Inicia a coleta rápida de luminosidade em tempo real."""
    global calibragem_luminosidade_ativa, _thread_calibragem
    if calibragem_luminosidade_ativa:
        return  # já está rodando

    calibragem_luminosidade_ativa = True

    def loop_calibragem():
        while calibragem_luminosidade_ativa:
            try:
                valor = arredondar(sensor.ler_luminosidade())
                enviar_dados_realtime(estufa_id, {"LuminosidadeAtual": valor})

                print(f"💡 Calibragem realtime → {valor:.2f} Lux")
            except Exception as e:
                print(f"⚠️ Erro calibragem luminosidade: {e}")
            time.sleep(1)  # coleta rápida

    _thread_calibragem = threading.Thread(target=loop_calibragem, daemon=True)
    _thread_calibragem.start()


def finalizar_calibragem_luminosidade():
    global calibragem_luminosidade_ativa
    if calibragem_luminosidade_ativa:
        calibragem_luminosidade_ativa = False
        print("✅ Calibragem de luminosidade finalizada.")
    else:
        return

# modules/atuadores/bomba.py
import RPi.GPIO as GPIO
from datetime import datetime
import threading


class Bomba:
    """
    Controla a bomba peristáltica da estufa com base na umidade do solo.

    Lógica de funcionamento:
      - Se OverrideUmidadeDoSolo estiver ativo → usa valor desejado.
      - Caso contrário → usa limites do preset (UmidadeDoSoloMin e UmidadeDoSoloMax).
      - Após cada irrigação, espera TEMPO_REACAO_UMIDADE antes de permitir nova ativação.
      - Sempre inicia desligada por segurança.

    Retorno do método `controlar`:
      - (True, motivo)  → bomba ligada.
      - (False, motivo) → bomba desligada.
    """

    # 🔧 Constantes calibráveis
    VAZAO_ML_POR_SEGUNDO = 1.31  # Vazão calibrada da bomba INTLLAB (~mL/s)
    VOLUME_POR_IRRIGACAO = 100  # Volume padrão por irrigação (mL)
    TEMPO_REACAO_UMIDADE = 120  # Tempo mínimo de espera após irrigação (s)

    def __init__(self, pino=22):
        """
        Inicializa a bomba no pino especificado.

        Parâmetros:
            pino (int): Número do pino BCM conectado ao módulo relé.
                        Default = 22.
        """
        self.pino = pino
        try:
            GPIO.setmode(GPIO.BCM)
            GPIO.setup(self.pino, GPIO.OUT)
        except Exception as e:
            print(f"⚠️ Erro ao inicializar GPIO da bomba: {e}")

        # atributos internos
        self.ultimo_acionamento = None
        self.is_irrigando = False
        self._timer = None

        self.desligar()  # inicializa desligada

    def ligar(self, duracao):
        """
        Liga a bomba por um tempo definido (segundos).
        Agenda desligamento automático com threading.Timer.

        Parâmetros:
            duracao (float): tempo em segundos para manter a bomba ligada.
        """
        if self.is_irrigando:
            return  # já está em irrigação

        self.is_irrigando = True
        try:
            GPIO.output(self.pino, GPIO.LOW)  # LOW = ligado (ajustar conforme hardware)
        except Exception as e:
            print(f"⚠️ Erro ao ligar bomba: {e}")
            self.is_irrigando = False
            return

        # agenda desligamento
        self._timer = threading.Timer(duracao, self.desligar)
        self._timer.start()
        self.ultimo_acionamento = datetime.now()

    def desligar(self):
        """Desliga a bomba imediatamente e cancela o timer se existir."""
        try:
            GPIO.output(self.pino, GPIO.HIGH)
        except Exception as e:
            print(f"⚠️ Erro ao desligar bomba: {e}")
        self.is_irrigando = False
        if self._timer:
            self._timer.cancel()
            self._timer = None

    def controlar(self, umidade_solo, config):
        """
        Decide se deve ligar a bomba com base na umidade do solo e configuração ativa.

        Parâmetros:
            umidade_solo (float|None): valor do sensor de umidade (%).
            config (dict): configuração ativa da estufa (preset + overrides).

        Retorna:
            tuple(bool, str):
                - bool: True se a bomba foi ligada, False caso contrário.
                - str: motivo da decisão.
        """
        if not isinstance(config, dict):
            self.desligar()
            return False, "Configuração inválida"

        if umidade_solo is None:
            self.desligar()
            return False, "Leitura inválida de umidade"

        # ⏱️ Verifica tempo desde última irrigação
        if self.ultimo_acionamento:
            tempo_passado = (datetime.now() - self.ultimo_acionamento).total_seconds()
            if tempo_passado < self.TEMPO_REACAO_UMIDADE:
                self.desligar()
                return (
                    False,
                    f"Aguardando reação ({int(tempo_passado)}s / {self.TEMPO_REACAO_UMIDADE}s)",
                )

        # 🧪 Override ativo
        if config.get("OverrideUmidadeDoSolo", False):
            umi_desejada = config.get("UmidadeDoSoloDesejada")
            if umi_desejada is not None and umidade_solo < umi_desejada:
                duracao = self._calcular_tempo_irrigacao()
                self.ligar(duracao)
                return (
                    True,
                    f"Override: {umidade_solo}% < {umi_desejada}% → irrigando {duracao:.2f}s",
                )
            else:
                self.desligar()
                return False, f"Override: Umidade adequada ({umidade_solo}%)"

        # 🌱 Lógica padrão (preset)
        umi_min = config.get("UmidadeDoSoloMin", 30)
        umi_max = config.get("UmidadeDoSoloMax", 80)

        if umi_min > umi_max:
            self.desligar()
            return (
                False,
                "Configuração inconsistente: UmidadeDoSoloMin > UmidadeDoSoloMax",
            )

        if umidade_solo < umi_min:
            duracao = self._calcular_tempo_irrigacao()
            self.ligar(duracao)
            return (
                True,
                f"Umidade baixa ({umidade_solo}% < {umi_min}%) → irrigando {duracao:.2f}s",
            )

        if umidade_solo > umi_max:
            self.desligar()
            return False, f"Solo muito úmido ({umidade_solo}% > {umi_max}%)"

        # Faixa adequada
        self.desligar()
        return False, f"Umidade adequada ({umidade_solo}%)"

    def _calcular_tempo_irrigacao(self):
        """Calcula o tempo necessário para entregar o volume configurado."""
        return self.VOLUME_POR_IRRIGACAO / self.VAZAO_ML_POR_SEGUNDO

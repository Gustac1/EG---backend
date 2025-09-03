import RPi.GPIO as GPIO
from datetime import datetime
import threading


class Bomba:
    """
    Controla a bomba peristáltica com base na umidade do solo.
    Evita travar a thread principal com time.sleep().
    """

    VAZAO_ML_POR_SEGUNDO = 1.31         # Vazão calibrada da bomba INTLLAB
    VOLUME_POR_IRRIGACAO = 100          # Volume padrão por irrigação (mL)
    TEMPO_REACAO_UMIDADE = 120        # Tempo de espera após irrigação (s) — 30 minutos 1800

    def __init__(self, pino=22):
        self.pino = pino
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(self.pino, GPIO.OUT)

        # inicializa atributos antes de qualquer método
        self.ultimo_acionamento = None
        self.is_irrigando = False
        self._timer = None

        self.desligar()

    def ligar(self, duracao):
        """Liga a bomba e agenda o desligamento automático."""
        if self.is_irrigando:
            return  # já está em irrigação

        self.is_irrigando = True
        GPIO.output(self.pino, GPIO.LOW)  # LOW = ligado (ajustar conforme hardware)

        # agenda desligamento automático
        self._timer = threading.Timer(duracao, self.desligar)
        self._timer.start()
        self.ultimo_acionamento = datetime.now()

    def desligar(self):
        """Desliga a bomba imediatamente."""
        GPIO.output(self.pino, GPIO.HIGH)
        self.is_irrigando = False
        if self._timer:
            self._timer.cancel()
            self._timer = None

    def controlar(self, umidade_solo, config):
        """
        Decide se deve ligar a bomba baseado na umidade e config.
        Retorna (estado, motivo).
        """
        if umidade_solo is None:
            self.desligar()
            return False, "Leitura inválida de umidade"

        # ⏱️ Verifica tempo desde última irrigação
        if self.ultimo_acionamento:
            tempo_passado = (datetime.now() - self.ultimo_acionamento).total_seconds()
            if tempo_passado < self.TEMPO_REACAO_UMIDADE:
                self.desligar()
                return False, f"Aguardando reação ({int(tempo_passado)}s / {self.TEMPO_REACAO_UMIDADE}s)"

        # 🧪 Override ativo
        if config.get("OverrideUmidadeDoSolo", False):
            umi_desejada = config.get("UmidadeDoSoloDesejada")
            if umi_desejada is not None and umidade_solo < umi_desejada:
                duracao = self._calcular_tempo_irrigacao()
                self.ligar(duracao)
                return True, f"Override: {umidade_solo}% < {umi_desejada}% → irrigando {duracao:.2f}s"
            else:
                self.desligar()
                return False, f"Override: Umidade adequada ({umidade_solo}%)"

        # 🌱 Lógica padrão
        umi_min = config.get("UmidadeDoSoloMin", 30)
        umi_max = config.get("UmidadeDoSoloMax", 80)

        if umidade_solo < umi_min:
            duracao = self._calcular_tempo_irrigacao()
            self.ligar(duracao)
            return True, f"Umidade baixa ({umidade_solo}% < {umi_min}%) → irrigando {duracao:.2f}s"

        if umidade_solo > umi_max:
            self.desligar()
            return False, f"Solo muito úmido ({umidade_solo}% > {umi_max}%)"

        self.desligar()
        return False, f"Umidade adequada ({umidade_solo}%)"

    def _calcular_tempo_irrigacao(self):
        """Calcula o tempo necessário para entregar o volume configurado."""
        return self.VOLUME_POR_IRRIGACAO / self.VAZAO_ML_POR_SEGUNDO

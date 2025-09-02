import RPi.GPIO as GPIO

class Ventoinha:
    """
    Controla o relé da ventoinha.

    Prioridade:
    1. Ligada com o aquecedor.
    2. Override de umidade → respeita valor desejado e ignora preset.
    3. Sem override → aplica limites máximos de temperatura/umidade.
    """

    def __init__(self, pino=27):
        self.pino = pino
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(self.pino, GPIO.OUT)
        self.desligar()

    def ligar(self):
        GPIO.output(self.pino, GPIO.LOW)

    def desligar(self):
        GPIO.output(self.pino, GPIO.HIGH)

    def controlar(self, temperatura_ar, umidade_ar, aquecedor_ativo, config):
        """
        Retorna:
        - (True, motivo) se ligada
        - (False, motivo) se desligada
        """

        # 🔥 1. Aquecedor tem prioridade
        if aquecedor_ativo:
            self.ligar()
            return True, "🟡 Ligada junto com o aquecedor"

        # ⚠️ 2. Validação
        if temperatura_ar is None or umidade_ar is None:
            return False, "⚠️ Leitura inválida de sensores"

        # 🧪 3. Override de umidade — aplica lógica exclusiva
        if config.get("OverrideUmidade", False):
            umi_desejada = config.get("UmidadeDesejada")
            if umi_desejada is not None:
                if umidade_ar > umi_desejada:
                    self.ligar()
                    return True, f"⚠️ Override: Umidade {umidade_ar}% > desejada ({umi_desejada}%)"
                else:
                    self.desligar()
                    return False, f"✅ Override: Umidade abaixo do limite ({umidade_ar}% ≤ desejada {umi_desejada}%)"

        # 🔧 4. Lógica com base nos presets
        temp_desejada = config.get("TemperaturaDesejada")
        temp_max = config.get("TemperaturaMax", 999)
        umi_max = config.get("UmidadeMax", 999)

        if temp_desejada is not None and temperatura_ar > temp_desejada:
            self.ligar()
            return True, f"⚠️ Temperatura {temperatura_ar}°C > desejada ({temp_desejada}°C)"

        if temperatura_ar >= temp_max:
            self.ligar()
            return True, f"🚨 Temperatura {temperatura_ar}°C ≥ limite ({temp_max}°C)"

        if umidade_ar >= umi_max:
            self.ligar()
            return True, f"🚨 Umidade {umidade_ar}% ≥ limite ({umi_max}%)"

        # ✅ 5. Tudo normal
        self.desligar()
        return False, "✅ Condições normais"

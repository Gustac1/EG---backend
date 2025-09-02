import RPi.GPIO as GPIO

class Aquecedor:
    """
    Classe responsável por controlar o relé do aquecedor com base em limites definidos no preset
    e valores desejados informados pelo usuário.

    A lógica segue:
    - Se 'TemperaturaDesejada' estiver definida e for maior que a temperatura atual → liga
    - Se não houver override, usa 'TemperaturaMin' e 'TemperaturaMax'
    - Se a temperatura estiver fora dos limites de segurança → envia alerta

    Retorno da função controlar():
    - (True, motivo) se ligado
    - (False, motivo) se desligado
    """

    def __init__(self, pino=10):
        self.pino = pino
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(self.pino, GPIO.OUT)
        self.desligar()

    def ligar(self):
        GPIO.output(self.pino, GPIO.LOW)

    def desligar(self):
        GPIO.output(self.pino, GPIO.HIGH)

    def controlar(self, temperatura_ar, config):
        """
        Controla o aquecedor com base na temperatura do ar e configuração.

        Parâmetros:
        - temperatura_ar: valor do sensor
        - config: dicionário da configuração local

        Retorna:
        - (True, motivo) se o aquecedor estiver ligado
        - (False, motivo) se estiver desligado
        """

        if temperatura_ar is None:
            self.desligar()
            return False, "⚠️ Temperatura inválida"

        temp_desejada = config.get("TemperaturaDesejada")
        temp_min = config.get("TemperaturaMin", 0)
        temp_max = config.get("TemperaturaMax", 999)

        # 🎯 Controle com override
        if temp_desejada is not None:
            if temperatura_ar < temp_desejada:
                self.ligar()
                return True, f"⚠️ {temperatura_ar}°C < desejada ({temp_desejada}°C)"
            else:
                self.desligar()
                return False, f"✅ {temperatura_ar}°C ≥ desejada ({temp_desejada}°C)"

        # 🔧 Controle com base nos limites do preset
        if temperatura_ar < temp_min:
            self.ligar()
            return True, f"⚠️ {temperatura_ar}°C < mínima ({temp_min}°C)"

        if temperatura_ar >= temp_max:
            self.desligar()
            return False, f"🚨 {temperatura_ar}°C ≥ máxima ({temp_max}°C)"

        self.desligar()
        return False, f"✅ {temperatura_ar}°C entre {temp_min}°C e {temp_max}°C"

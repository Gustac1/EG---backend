import adafruit_dht
import board
import time


class DHT22:
    def __init__(self, pin=board.D17):  # Define GPIO padrão como 17
        """Inicializa o sensor DHT22 no pino especificado."""
        self.sensor = adafruit_dht.DHT22(pin)

    def ler_dados(self):
        """Lê temperatura e umidade do sensor."""
        try:
            temperatura = self.sensor.temperature
            umidade = self.sensor.humidity
            if temperatura is not None and umidade is not None:
                return temperatura, umidade
            else:
                return None, None
        except RuntimeError as e:
            print(f"Erro na leitura do sensor: {e}")
            return None, None

    def iniciar_leitura_continua(self, intervalo=5):
        """Lê os dados do sensor continuamente em intervalos definidos."""
        try:
            while True:
                temperatura, umidade = self.ler_dados()
                if temperatura is not None and umidade is not None:
                    print(f"Temperatura: {temperatura:.2f}°C | Umidade: {umidade:.2f}%")
                else:
                    print("Falha na leitura. Tentando novamente...")

                time.sleep(intervalo)
        except KeyboardInterrupt:
            print("\nLeitura interrompida pelo usuário.")


if __name__ == "__main__":
    dht_sensor = DHT22(pin=board.D17)  # Define GPIO 17
    dht_sensor.iniciar_leitura_continua(intervalo=2)  # Lendo a cada 5 segundos

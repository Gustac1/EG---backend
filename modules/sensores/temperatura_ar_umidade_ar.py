# modules/sensores/temperatura_ar_umidade_ar.py
import adafruit_dht
import board
import time


class DHT22:
    """
    Driver para o sensor DHT22 (AM2302).

    Mede:
      - 🌡️ Temperatura do ar (°C)
      - 💧 Umidade relativa do ar (%)

    Observações:
      - Intervalo mínimo recomendado entre leituras: 2–3s.
      - Leituras falhas são comuns → usar tentativas múltiplas no controle.
    """

    def __init__(self, pin=board.D17):
        """
        Inicializa o sensor DHT22 no pino especificado.

        Parâmetros:
            pin: pino de dados do Raspberry Pi (default = GPIO17).
        """
        self.sensor = adafruit_dht.DHT22(pin)

    def ler_dados(self):
        """
        Lê a temperatura e a umidade do ar.

        Retorna:
            tuple(float|None, float|None):
                - (temperatura, umidade) se leitura bem-sucedida.
                - (None, None) em caso de erro.
        """
        try:
            temperatura = self.sensor.temperature
            umidade = self.sensor.humidity
            if temperatura is not None and umidade is not None:
                return temperatura, umidade
            return None, None

        except RuntimeError as e:
            print(f"⚠️ Erro na leitura do DHT22: {e}")
            return None, None
        except OverflowError as e:
            print(f"⚠️ Overflow na leitura do DHT22: {e}")
            return None, None
        except Exception as e:
            print(f"⚠️ Erro inesperado no DHT22: {e}")
            return None, None

    def iniciar_leitura_continua(self, intervalo=5):
        """
        Executa leitura contínua em intervalos definidos.

        Parâmetros:
            intervalo (int): intervalo entre leituras (segundos).
                             Mínimo recomendado: 3s.
        """
        try:
            while True:
                temperatura, umidade = self.ler_dados()
                if temperatura is not None and umidade is not None:
                    print(f"🌡️ {temperatura:.2f}°C | 💧 {umidade:.2f}%")
                else:
                    print("❌ Falha na leitura. Tentando novamente...")

                time.sleep(max(3, intervalo))
        except KeyboardInterrupt:
            print("\n⛔ Leitura interrompida pelo usuário.")
        finally:
            self.close()

    def close(self):
        """Libera os recursos do sensor."""
        try:
            self.sensor.exit()
        except Exception:
            pass


# ====== TESTE AUTOMÁTICO ======
if __name__ == "__main__":
    dht_sensor = DHT22(pin=board.D17)
    dht_sensor.iniciar_leitura_continua(intervalo=3)

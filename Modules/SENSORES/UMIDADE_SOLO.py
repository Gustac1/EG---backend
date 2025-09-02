import time
import board
import busio
import adafruit_ads1x15.ads1115 as ADS
from adafruit_ads1x15.analog_in import AnalogIn

class UmidadeSolo:
    def __init__(self, canal=ADS.P0):
        """ Inicializa o sensor de umidade do solo utilizando o ADS1115 """
        self.i2c = busio.I2C(board.SCL, board.SDA)
        self.ads = ADS.ADS1115(self.i2c)
        self.canal_umidade = AnalogIn(self.ads, canal)

    def ler_umidade(self):
        """Lê o valor analógico do sensor capacitivo e converte para porcentagem"""
        leitura = self.canal_umidade.value  # Obtém o valor cru (0 - 65535)

        # Calibração do sensor (ajuste os valores para seu caso específico)
        seco = 25000  # Valor do sensor no solo seco
        molhado = 12000  # Valor do sensor no solo úmido

        # Convertendo para uma escala de 0% (seco) a 100% (molhado)
        umidade = 100 - ((leitura - molhado) / (seco - molhado) * 100)
        umidade = max(0, min(100, umidade))  # Mantém entre 0% e 100%

        return round(umidade, 2)  # Retorna o valor arredondado para 2 casas decimais

if __name__ == "__main__":
    sensor_umidade = UmidadeSolo()
    try:
        while True:
            umidade = sensor_umidade.ler_umidade()
            print(f"Umidade do solo: {umidade:.2f}%")
            time.sleep(2)
    except KeyboardInterrupt:
        print("\nEncerrando...")

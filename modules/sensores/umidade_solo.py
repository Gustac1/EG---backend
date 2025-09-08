# modules/sensores/umidade_solo.py
import time
import board
import busio
import adafruit_ads1x15.ads1115 as ADS
from adafruit_ads1x15.analog_in import AnalogIn


class UmidadeSolo:
    """
    Driver para o sensor capacitivo de umidade do solo via ADS1115.

    Funcionamento:
      - Lê valor analógico bruto (0–65535).
      - Converte para porcentagem (%), calibrado entre valores de solo seco e úmido.
      - Mantém saída entre 0% e 100%.
    """

    def __init__(self, canal=ADS.P0, seco=25000, molhado=12000):
        """
        Inicializa o sensor de umidade do solo.

        Parâmetros:
            canal: canal analógico do ADS1115 (default = ADS.P0).
            seco (int): valor lido no solo seco (ajustar conforme calibração).
            molhado (int): valor lido no solo úmido (ajustar conforme calibração).
        """
        try:
            self.i2c = busio.I2C(board.SCL, board.SDA)
            self.ads = ADS.ADS1115(self.i2c)
            self.canal_umidade = AnalogIn(self.ads, canal)
        except Exception as e:
            print(f"⚠️ Erro ao inicializar ADS1115: {e}")
            self.canal_umidade = None

        # valores de calibração
        self.seco = seco
        self.molhado = molhado

    def ler_umidade(self):
        """
        Lê o valor de umidade do solo em porcentagem.

        Retorna:
            float | None:
                - Valor de umidade (%), arredondado para 2 casas decimais.
                - None, em caso de erro ou falha de leitura.
        """
        if not self.canal_umidade:
            return None
        try:
            leitura = self.canal_umidade.value  # valor cru (0–65535)

            # Converte para escala calibrada
            umidade = 100 - (
                (leitura - self.molhado) / (self.seco - self.molhado) * 100
            )
            umidade = max(0, min(100, umidade))  # mantém entre 0% e 100%

            return round(umidade, 2)
        except Exception as e:
            print(f"⚠️ Erro ao ler umidade do solo: {e}")
            return None

    def close(self):
        """Método de fechamento (mantido por consistência, não necessário para ADS1115)."""
        pass


# ====== TESTE AUTOMÁTICO ======
if __name__ == "__main__":
    sensor_umidade = UmidadeSolo()
    try:
        while True:
            umidade = sensor_umidade.ler_umidade()
            if umidade is not None:
                print(f"🌱 Umidade do solo: {umidade:.2f}%")
            else:
                print("❌ Falha ao ler sensor de umidade do solo")
            time.sleep(2)
    except KeyboardInterrupt:
        print("\n⛔ Leitura interrompida pelo usuário.")

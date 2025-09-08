# modules/sensores/temperatura_solo.py
import glob
import time


class DS18B20:
    """
    Driver para o sensor DS18B20 (temperatura do solo) via 1-Wire.

    Funcionamento:
      - O sensor aparece em /sys/bus/w1/devices/ com prefixo "28-".
      - A leitura é feita no arquivo "w1_slave".
      - A validação é feita via CRC ("YES" no final da primeira linha).
      - Retorna a temperatura em °C, ou None em caso de falha.
    """

    def __init__(self):
        """
        Inicializa o DS18B20, identificando o diretório do dispositivo.
        """
        base_dir = "/sys/bus/w1/devices/"
        device_folders = glob.glob(base_dir + "28*")
        if device_folders:
            self.device_file = device_folders[0] + "/w1_slave"
        else:
            self.device_file = None
            print("⚠️ DS18B20 não encontrado no boot. (verifique conexões e 1-Wire)")

    def read_temp_raw(self):
        """
        Lê os dados brutos do sensor (duas linhas de texto).

        Retorna:
            list[str] | None:
                - Linhas do arquivo w1_slave.
                - None em caso de erro ou sensor não encontrado.
        """
        if not self.device_file:
            return None
        try:
            with open(self.device_file, "r") as f:
                return f.readlines()
        except Exception as e:
            print(f"⚠️ Erro ao ler DS18B20: {e}")
            return None

    def read_temp(self):
        """
        Processa os dados e retorna a temperatura em °C.

        Retorna:
            float | None:
                - Temperatura em °C se a leitura for válida.
                - None em caso de falha.
        """
        lines = self.read_temp_raw()
        if not lines:
            return None

        # Verifica integridade até 3 tentativas
        retries = 3
        while lines and lines[0].strip()[-3:] != "YES" and retries > 0:
            time.sleep(0.2)
            lines = self.read_temp_raw()
            retries -= 1
        if not lines or retries == 0:
            return None

        # Extrai temperatura
        equals_pos = lines[1].find("t=")
        if equals_pos != -1:
            try:
                temp_string = lines[1][equals_pos + 2 :]
                temp_c = float(temp_string) / 1000.0
                return temp_c
            except Exception as e:
                print(f"⚠️ Erro ao converter leitura do DS18B20: {e}")
                return None

        return None

    def close(self):
        """Método de fechamento (mantido por consistência, não necessário no DS18B20)."""
        pass


# ====== TESTE AUTOMÁTICO ======
if __name__ == "__main__":
    sensor = DS18B20()
    while True:
        temp = sensor.read_temp()
        if temp is not None:
            print(f"🌱 Temperatura do Solo: {temp:.2f}°C")
        else:
            print("❌ Falha ao ler DS18B20")
        time.sleep(2)

import os
import glob
import time

class DS18B20:
    def __init__(self):
        """Inicializa o sensor DS18B20, identificando o diretório do dispositivo."""
        base_dir = "/sys/bus/w1/devices/"
        device_folders = glob.glob(base_dir + "28*")
        if device_folders:
            self.device_file = device_folders[0] + "/w1_slave"
        else:
            raise FileNotFoundError("Sensor DS18B20 não encontrado!")

    def read_temp_raw(self):
        """Lê os dados brutos do sensor."""
        try:
            with open(self.device_file, "r") as f:
                return f.readlines()
        except Exception as e:
            print(f"Erro ao ler o sensor DS18B20: {e}")
            return None

    def read_temp(self):
        """Processa os dados e retorna a temperatura em °C."""
        lines = self.read_temp_raw()
        if not lines:
            return None
        
        while lines[0].strip()[-3:] != "YES":
            time.sleep(0.2)
            lines = self.read_temp_raw()

        equals_pos = lines[1].find("t=")
        if equals_pos != -1:
            temp_string = lines[1][equals_pos + 2 :]
            temp_c = float(temp_string) / 1000.0
            return temp_c  # Retorna apenas a temperatura em °C

        return None

# Teste isolado (apenas se executar este arquivo diretamente)
if __name__ == "__main__":
    sensor = DS18B20()
    while True:
        temp = sensor.read_temp()
        print(f"Temperatura do Solo: {temp:.2f}°C")
        time.sleep(2)

# modules/sensores/luminosidade.py
import smbus2
import time


class BH1750:
    """
    Driver para o sensor de luminosidade BH1750 via I²C.

    Funcionamento:
      - Mede a intensidade de luz ambiente em lux.
      - Usa modo de medição contínuo em alta resolução (0x10).
      - Requer ~120ms de tempo de conversão após o comando.

    Uso:
        sensor = BH1750()
        lux = sensor.ler_luminosidade()
        sensor.close()
    """

    ENDERECO_I2C = 0x23  # Endereço padrão do BH1750
    MODO_MEDICAO = 0x10  # Alta resolução (1 lx / 1.2)

    def __init__(self, bus=1, address=ENDERECO_I2C):
        """
        Inicializa o sensor BH1750.

        Parâmetros:
            bus (int): número do barramento I²C (default = 1).
            address (hex): endereço do sensor no barramento.
        """
        self.bus = smbus2.SMBus(bus)
        self.address = address

    def ler_luminosidade(self):
        """
        Lê o nível de luminosidade em lux.

        Retorna:
            float | None:
                - Valor da luminosidade em lux, se leitura bem-sucedida.
                - None, em caso de erro.
        """
        try:
            self.bus.write_byte(self.address, self.MODO_MEDICAO)  # envia comando
            time.sleep(0.2)  # aguarda conversão (~120ms)

            data = self.bus.read_i2c_block_data(self.address, 0, 2)  # lê 2 bytes
            nivel_luminosidade = (data[0] << 8) | data[1]  # converte p/ decimal
            return nivel_luminosidade / 1.2  # fator de correção

        except Exception as e:
            print(f"⚠️ Erro ao ler BH1750: {e}")
            return None

    def close(self):
        """Fecha a comunicação com o barramento I²C."""
        try:
            self.bus.close()
        except Exception as e:
            print(f"⚠️ Erro ao fechar comunicação BH1750: {e}")


# ====== TESTE AUTOMÁTICO AO EXECUTAR O SCRIPT ======
if __name__ == "__main__":
    sensor = BH1750()
    try:
        print("Iniciando teste do sensor BH1750. Pressione Ctrl + C para sair.\n")
        while True:
            lux = sensor.ler_luminosidade()
            if lux is not None:
                print(f"🌞 Luminosidade: {lux:.2f} lux")
            else:
                print("⚠️ Erro na leitura da luminosidade.")

            time.sleep(1)
    except KeyboardInterrupt:
        print("\nTeste encerrado. Fechando a comunicação com o sensor.")
        sensor.close()

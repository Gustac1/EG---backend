import smbus2
import time

class BH1750:
    
    EnderecoI2C = 0x23 # Endereço padrão do BH1750 no I2C e com conexão direta com o GND
    ModoDeMedicao = 0x10 # Modo de medição de alta resolução

    def __init__(self, bus=1, address=EnderecoI2C):
        self.bus = smbus2.SMBus(bus) # Abre a comunicação I2C
        self.address = address # Define o endereço do SENSORES

    def ler_luminosidade(self):
        try:
            self.bus.write_byte(self.address, self.ModoDeMedicao)  # Envia o comando de leitura
            time.sleep(0.2) # Aguarda os dados

            data=self.bus.read_i2c_block_data(self.address,0,2) # Lê dos bytes do sensor em hexadecimal
            NivelDeLuminosidade = (data[0] <<8) | data[1] # Converte os bytes para decimal
            return NivelDeLuminosidade / 1.2 # Aplica fator de correção amplamente utilizado pela comunidade

        except Exception as e:

            print(f"Erro ao ler o sensor BH1750: {e}")
            return None
    
    def close(self):
        self.bus.close() #Fecha a comunicação I2C


# ====== TESTE AUTOMÁTICO AO EXECUTAR O SCRIPT ======
if __name__ == "__main__":
    sensor = BH1750()
    try:
        print("Iniciando teste do sensor BH1750. Pressione Ctrl + C para sair.\n")
        while True:
            lux = sensor.ler_luminosidade()
            if lux is not None:
                print(f"Luminosidade: {lux:.2f} lux")
            else:
                print("Erro na leitura da luminosidade.")
            
            time.sleep(1)  # Aguarda 1 segundo entre leituras
    except KeyboardInterrupt:
        print("\nTeste encerrado. Fechando a comunicação com o sensor.")
        sensor.close()
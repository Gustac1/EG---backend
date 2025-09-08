# modules/atuadores/aquecedor.py
import RPi.GPIO as GPIO


class Aquecedor:
    """
    Classe de controle do relé do aquecedor da estufa.

    Lógica de funcionamento:
      - Se "TemperaturaDesejada" estiver definida → usa este valor como alvo.
      - Caso contrário → usa limites do preset ("TemperaturaMin" e "TemperaturaMax").
      - Sempre inicia desligado por segurança.
      - Se ocorrer erro de leitura ou configuração inválida → permanece desligado.

    Retornos do método `controlar`:
      - (True, motivo)  → aquecedor ligado.
      - (False, motivo) → aquecedor desligado.
    """

    def __init__(self, pino=10):
        """
        Inicializa o relé do aquecedor.

        Parâmetros:
            pino (int): Número do pino BCM conectado ao módulo relé.
                        Default = 10.
        """
        self.pino = pino
        try:
            GPIO.setmode(GPIO.BCM)
            GPIO.setup(self.pino, GPIO.OUT)
        except Exception as e:
            print(f"⚠️ Erro ao inicializar GPIO do aquecedor: {e}")
        self.desligar()  # inicializa desligado por segurança

    def ligar(self):
        """Liga o aquecedor (nível lógico LOW no relé)."""
        try:
            GPIO.output(self.pino, GPIO.LOW)
        except Exception as e:
            print(f"⚠️ Erro ao ligar aquecedor: {e}")

    def desligar(self):
        """Desliga o aquecedor (nível lógico HIGH no relé)."""
        try:
            GPIO.output(self.pino, GPIO.HIGH)
        except Exception as e:
            print(f"⚠️ Erro ao desligar aquecedor: {e}")

    def controlar(self, temperatura_ar, config):
        """
        Controla o aquecedor com base na temperatura do ar e configuração ativa.

        Parâmetros:
            temperatura_ar (float|None): temperatura do ar medida pelo sensor (°C).
            config (dict): configuração ativa da estufa (preset + overrides).

        Retorna:
            tuple(bool, str):
                - bool: True se o aquecedor foi ligado, False caso contrário.
                - str: motivo da decisão.
        """
        # Verificação de config
        if not isinstance(config, dict):
            self.desligar()
            return False, "Configuração inválida"

        # Verificação de temperatura
        if temperatura_ar is None:
            self.desligar()
            return False, "Temperatura inválida"

        temp_desejada = config.get("TemperaturaDesejada")
        temp_min = config.get("TemperaturaMin", 0)
        temp_max = config.get("TemperaturaMax", 999)

        # Corrige inconsistência de preset
        if temp_min > temp_max:
            print("⚠️ Configuração inconsistente: TemperaturaMin > TemperaturaMax")
            self.desligar()
            return False, "Configuração inconsistente"

        # 🎯 Controle com override (valor desejado do usuário)
        if temp_desejada is not None:
            if temperatura_ar < temp_desejada:
                self.ligar()
                return True, f"{temperatura_ar}°C < desejada ({temp_desejada}°C)"
            else:
                self.desligar()
                return False, f"{temperatura_ar}°C ≥ desejada ({temp_desejada}°C)"

        # 🔧 Controle com base nos limites do preset
        if temperatura_ar < temp_min:
            self.ligar()
            return True, f"{temperatura_ar}°C < mínima ({temp_min}°C)"

        if temperatura_ar >= temp_max:
            self.desligar()
            return False, f"{temperatura_ar}°C ≥ máxima ({temp_max}°C)"

        # Faixa intermediária → mantém desligado
        self.desligar()
        return False, f"{temperatura_ar}°C entre {temp_min}°C e {temp_max}°C"

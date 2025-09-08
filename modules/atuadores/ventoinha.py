# modules/atuadores/ventoinha.py
import RPi.GPIO as GPIO


class Ventoinha:
    """
    Controla a ventoinha da estufa com base em temperatura e umidade.

    Prioridade de acionamento:
      1. Sempre ligada junto com o aquecedor (garante circulação de ar).
      2. Override ativo → segue valor desejado de umidade, ignorando presets.
      3. Caso contrário → aplica limites de temperatura e umidade do preset.

    Retorno do método `controlar`:
      - (True, motivo)  → ventoinha ligada.
      - (False, motivo) → ventoinha desligada.
    """

    def __init__(self, pino=27):
        """
        Inicializa a ventoinha no pino especificado.

        Parâmetros:
            pino (int): Número do pino BCM conectado ao relé.
                        Default = 27.
        """
        self.pino = pino
        try:
            GPIO.setmode(GPIO.BCM)
            GPIO.setup(self.pino, GPIO.OUT)
        except Exception as e:
            print(f"⚠️ Erro ao inicializar GPIO da ventoinha: {e}")
        self.desligar()

    def ligar(self):
        """Liga a ventoinha (nível lógico LOW no relé)."""
        try:
            GPIO.output(self.pino, GPIO.LOW)
        except Exception as e:
            print(f"⚠️ Erro ao ligar ventoinha: {e}")

    def desligar(self):
        """Desliga a ventoinha (nível lógico HIGH no relé)."""
        try:
            GPIO.output(self.pino, GPIO.HIGH)
        except Exception as e:
            print(f"⚠️ Erro ao desligar ventoinha: {e}")

    def controlar(self, temperatura_ar, umidade_ar, aquecedor_ativo, config):
        """
        Decide o estado da ventoinha com base nas leituras e na configuração.

        Parâmetros:
            temperatura_ar (float|None): Temperatura do ar medida (°C).
            umidade_ar (float|None): Umidade do ar medida (%).
            aquecedor_ativo (bool): Indica se o aquecedor está ligado.
            config (dict): Configuração ativa (preset + overrides).

        Retorna:
            tuple(bool, str):
                - bool: True se ligada, False se desligada.
                - str: motivo da decisão.
        """
        if not isinstance(config, dict):
            self.desligar()
            return False, "Configuração inválida"

        # 🔥 1. Aquecedor tem prioridade
        if aquecedor_ativo:
            self.ligar()
            return True, "Ligada junto com o aquecedor"

        # ⚠️ 2. Validação de sensores
        if temperatura_ar is None or umidade_ar is None:
            self.desligar()
            return False, "Leitura inválida de sensores"

        # 🧪 3. Override de umidade
        if config.get("OverrideUmidade", False):
            umi_desejada = config.get("UmidadeDesejada")
            if umi_desejada is not None:
                if umidade_ar > umi_desejada:
                    self.ligar()
                    return (
                        True,
                        f"Override: Umidade {umidade_ar}% > desejada ({umi_desejada}%)",
                    )
                else:
                    self.desligar()
                    return (
                        False,
                        f"Override: Umidade adequada ({umidade_ar}% ≤ {umi_desejada}%)",
                    )

        # 🔧 4. Lógica de preset
        temp_desejada = config.get("TemperaturaDesejada")
        temp_max = config.get("TemperaturaMax", 999)
        umi_max = config.get("UmidadeMax", 999)

        # Verifica consistência de limites
        if temp_desejada is not None and temp_desejada > temp_max:
            print("⚠️ Configuração inconsistente: TemperaturaDesejada > TemperaturaMax")
            self.desligar()
            return False, "Configuração inconsistente"

        if temp_desejada is not None and temperatura_ar > temp_desejada:
            self.ligar()
            return (
                True,
                f"Temperatura {temperatura_ar}°C > desejada ({temp_desejada}°C)",
            )

        if temperatura_ar >= temp_max:
            self.ligar()
            return True, f"Temperatura {temperatura_ar}°C ≥ limite ({temp_max}°C)"

        if umidade_ar >= umi_max:
            self.ligar()
            return True, f"Umidade {umidade_ar}% ≥ limite ({umi_max}%)"

        # ✅ 5. Condições normais → desligada
        self.desligar()
        return False, "Condições normais"

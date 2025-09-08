# modules/atuadores/luminaria.py
import RPi.GPIO as GPIO
from datetime import datetime, timedelta


class Luminaria:
    """
    Controla a luminária da estufa com base no fotoperíodo configurado.

    Funcionamento:
      - A luminária sempre inicia às 06:00.
      - É desligada após 'Fotoperiodo' horas.
      - Se 'Fotoperiodo' >= 24 → permanece ligada continuamente.
      - Considera o caso de ciclos que atravessam a meia-noite.

    Retorno do método `controlar`:
      - (True, motivo)  → luminária ligada.
      - (False, motivo) → luminária desligada.
    """

    HORA_INICIO = "06:00"  # horário fixo de início do fotoperíodo

    def __init__(self, pino=9):
        """
        Inicializa a luminária no pino especificado.

        Parâmetros:
            pino (int): Número do pino BCM conectado ao relé.
                        Default = 9.
        """
        self.pino = pino
        try:
            GPIO.setmode(GPIO.BCM)
            GPIO.setup(self.pino, GPIO.OUT)
        except Exception as e:
            print(f"⚠️ Erro ao inicializar GPIO da luminária: {e}")
        self.desligar()

    def ligar(self):
        """Liga a luminária (nível lógico LOW no relé)."""
        try:
            GPIO.output(self.pino, GPIO.LOW)
        except Exception as e:
            print(f"⚠️ Erro ao ligar luminária: {e}")

    def desligar(self):
        """Desliga a luminária (nível lógico HIGH no relé)."""
        try:
            GPIO.output(self.pino, GPIO.HIGH)
        except Exception as e:
            print(f"⚠️ Erro ao desligar luminária: {e}")

    def controlar(self, config):
        """
        Controla a luminária com base no horário atual e no fotoperíodo definido.

        Parâmetros:
            config (dict): configuração ativa da estufa (deve conter 'Fotoperiodo').

        Retorna:
            tuple(bool, str):
                - bool: True se a luminária foi ligada, False caso contrário.
                - str: motivo da decisão.
        """
        if not isinstance(config, dict):
            self.desligar()
            return False, "Configuração inválida"

        fotoperiodo = config.get("Fotoperiodo", 12)
        hora_atual = datetime.now().time()

        hora_inicio = datetime.strptime(self.HORA_INICIO, "%H:%M").time()
        hora_fim_dt = datetime.combine(datetime.today(), hora_inicio) + timedelta(
            hours=fotoperiodo
        )
        hora_fim = hora_fim_dt.time()

        # 🌞 Caso especial: 24h
        if fotoperiodo >= 24:
            self.ligar()
            return True, "Fotoperíodo 24h — ligada continuamente"

        # Caso normal (sem cruzar meia-noite)
        if hora_inicio <= hora_fim:
            if hora_inicio <= hora_atual <= hora_fim:
                self.ligar()
                return (
                    True,
                    f"Dentro do fotoperíodo (06:00 → {hora_fim.strftime('%H:%M')})",
                )
            else:
                self.desligar()
                return (
                    False,
                    f"Fora do fotoperíodo (06:00 → {hora_fim.strftime('%H:%M')})",
                )

        # Caso cruzando a meia-noite
        else:
            if hora_atual >= hora_inicio or hora_atual <= hora_fim:
                self.ligar()
                return (
                    True,
                    f"Dentro do fotoperíodo cruzando a meia-noite (06:00 → {hora_fim.strftime('%H:%M')})",
                )
            else:
                self.desligar()
                return (
                    False,
                    f"Fora do fotoperíodo cruzando a meia-noite (06:00 → {hora_fim.strftime('%H:%M')})",
                )

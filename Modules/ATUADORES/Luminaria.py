import RPi.GPIO as GPIO
from datetime import datetime, timedelta

class Luminaria:
    """
    Controla o relé da luminária com base no fotoperíodo.

    A luminária é ativada sempre às 06:00 e desativada após o número de horas
    definidas no parâmetro 'Fotoperiodo' vindo do config local.

    Retorna:
    - (True, motivo) se ligada
    - (False, motivo) se desligada
    """

    def __init__(self, pino=9):
        self.pino = pino
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(self.pino, GPIO.OUT)
        self.desligar()

    def ligar(self):
        GPIO.output(self.pino, GPIO.LOW)

    def desligar(self):
        GPIO.output(self.pino, GPIO.HIGH)

    def controlar(self, config):
        """
        Controla a luminária com base no horário atual e no fotoperíodo configurado.

        Parâmetros:
        - config: dicionário da configuração local

        Retorna:
        - (True, motivo) se ligada
        - (False, motivo) se desligada
        """
        fotoperiodo = config.get("Fotoperiodo", 12)
        hora_atual = datetime.now().time()

        hora_inicio = datetime.strptime("06:00", "%H:%M").time()
        hora_fim_dt = datetime.combine(datetime.today(), hora_inicio) + timedelta(hours=fotoperiodo)
        hora_fim = hora_fim_dt.time()

        if fotoperiodo >= 24:
            self.ligar()
            return True, "Fotoperíodo 24h — ligada continuamente"

        if hora_inicio <= hora_fim:
            if hora_inicio <= hora_atual <= hora_fim:
                self.ligar()
                return True, f"Dentro do fotoperíodo (06:00 → {hora_fim.strftime('%H:%M')})"
            else:
                self.desligar()
                return False, f"Fora do fotoperíodo (06:00 → {hora_fim.strftime('%H:%M')})"
        else:
            # Ciclo atravessa a meia-noite
            if hora_atual >= hora_inicio or hora_atual <= hora_fim:
                self.ligar()
                return True, f"Dentro do fotoperíodo cruzando a meia-noite (06:00 → {hora_fim.strftime('%H:%M')})"
            else:
                self.desligar()
                return False, f"Fora do fotoperíodo cruzando a meia-noite (06:00 → {hora_fim.strftime('%H:%M')})"

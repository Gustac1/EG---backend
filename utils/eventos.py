# utils/eventos.py
"""
Eventos globais usados em todo o backend.
Mantém centralizado para evitar import circular.
"""

import threading

# Evento global para resetar o ciclo de forma imediata
ciclo_reset_event = threading.Event()

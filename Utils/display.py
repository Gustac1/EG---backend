# Utils/display.py
import os
from datetime import datetime

def exibir_bloco_sensores(dados):
    """Exibe no terminal os dados atuais dos sensores em formato de painel."""
    hora = datetime.now().strftime("%H:%M:%S")
    print(f"\n{'='*20} 🌡️  Leitura Atual dos Sensores  [{hora}] {'='*20}\n")

    lux = dados.get("LuminosidadeAtual")
    print("☀️  Luminosidade")
    print(f"   • {lux:.2f} Lux\n" if lux is not None else "   • -- Lux\n")

    temp_ar = dados.get("TemperaturaDoArAtual")
    umi_ar = dados.get("UmidadeDoArAtual")
    print("🌬️  Ambiente (Ar)")
    print(f"   • Temperatura: {f'{temp_ar:.2f} °C' if temp_ar is not None else '-- °C'}")
    print(f"   • Umidade:     {f'{umi_ar:.2f} %' if umi_ar is not None else '-- %'}\n")

    temp_solo = dados.get("TemperaturaDoSoloAtual")
    umi_solo = dados.get("UmidadeDoSoloAtual")
    print("🌱  Solo")
    print(f"   • Temperatura: {f'{temp_solo:.2f} °C' if temp_solo is not None else '-- °C'}")
    print(f"   • Umidade:     {f'{umi_solo:.2f} %' if umi_solo is not None else '-- %'}\n")
    print("="*85)


def exibir_dados_periodicos(dados):
    """Exibe no terminal os dados médios enviados ao Firestore."""
    hora = datetime.now().strftime("%H:%M:%S")
    print(f"\n{'='*20} 🗂️  Média Enviada ao Firestore  [{hora}] {'='*20}\n")

    def formatar(chave, valor):
        if "Temperatura" in chave: return f"{valor:.2f} °C"
        if "Umidade" in chave: return f"{valor:.2f} %"
        if "Luminosidade" in chave: return f"{valor:.2f} Lux"
        return f"{valor}"

    for chave, valor in dados.items():
        if chave != "timestamp":
            print(f"📌 {chave:<25}: {formatar(chave, valor)}")

    print("="*85)


def exibir_status_atuadores(status_dict):
    """Exibe o status (ligado/desligado) de cada atuador com o motivo."""
    hora = datetime.now().strftime("%H:%M:%S")
    print(f"\n{'='*20} 🔧 Status dos Atuadores  [{hora}] {'='*20}\n")

    icones = {"Aquecedor": "🔥", "Ventoinha": "🌀", "Luminária": "💡", "Bomba": "💧"}
    for nome, (ligado, motivo) in status_dict.items():
        status_str = "LIGADO" if ligado else "DESLIGADO"
        print(f"{icones.get(nome, '🔘')} {nome:<16}: {status_str:<10} | {motivo}")

    print("="*85)

def limpar_terminal():
    os.system("cls" if os.name == "nt" else "clear")
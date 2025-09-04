# Utils/display.py
import os
from datetime import datetime, timezone
from Config.configuracao_local import carregar_preset
from dateutil.parser import isoparse
from Utils.logger import warn


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
    print(
        f"   • Temperatura: {f'{temp_ar:.2f} °C' if temp_ar is not None else '-- °C'}"
    )
    print(f"   • Umidade:     {f'{umi_ar:.2f} %' if umi_ar is not None else '-- %'}\n")

    temp_solo = dados.get("TemperaturaDoSoloAtual")
    umi_solo = dados.get("UmidadeDoSoloAtual")
    print("🌱  Solo")
    print(
        f"   • Temperatura: {f'{temp_solo:.2f} °C' if temp_solo is not None else '-- °C'}"
    )
    print(
        f"   • Umidade:     {f'{umi_solo:.2f} %' if umi_solo is not None else '-- %'}\n"
    )
    print("=" * 85)


def exibir_dados_periodicos(dados):
    """Exibe no terminal os dados médios enviados ao Firestore."""
    hora = datetime.now().strftime("%H:%M:%S")
    print(f"\n{'='*20} 🗂️  Média Enviada ao Firestore  [{hora}] {'='*20}\n")

    def formatar(chave, valor):
        if "Temperatura" in chave:
            return f"{valor:.2f} °C"
        if "Umidade" in chave:
            return f"{valor:.2f} %"
        if "Luminosidade" in chave:
            return f"{valor:.2f} Lux"
        return f"{valor}"

    for chave, valor in dados.items():
        if chave != "timestamp":
            print(f"📌 {chave:<25}: {formatar(chave, valor)}")

    print("=" * 85)


def exibir_status_atuadores(status_dict):
    """Exibe o status (ligado/desligado) de cada atuador com o motivo."""
    hora = datetime.now().strftime("%H:%M:%S")
    print(f"\n{'='*20} 🔧 Status dos Atuadores  [{hora}] {'='*20}\n")

    icones = {"Aquecedor": "🔥", "Ventoinha": "🌀", "Luminária": "💡", "Bomba": "💧"}
    for nome, (ligado, motivo) in status_dict.items():
        status_str = "LIGADO" if ligado else "DESLIGADO"
        print(f"{icones.get(nome, '🔘')} {nome:<16}: {status_str:<10} | {motivo}")

    print("=" * 85)


def exibir_status_fase(config):
    """Exibe informações da fase atual da planta."""
    try:
        planta = config.get("PlantaAtual")
        fase = config.get("FaseAtual")
        inicio_ts = config.get("InicioFaseTimestamp")

        if not planta or not fase:
            return
        hora = datetime.now().strftime("%H:%M:%S")

        if fase == "Colheita":
            print(f"\n{'='*20} 🌾  Fase Atual da Estufa  [{hora}] {'='*20}\n")
            print(f"📌 Planta selecionada      : {planta}")
            print(f"📖 Fase atual              : {fase}")
            print(f"📴 Sistema finalizado. Nenhum controle ativo.")
            print("=" * 85)
            return

        if fase == "Standby":
            print(f"\n{'='*20} ⏸️  Fase Atual da Estufa  [{hora}] {'='*20}\n")
            print(f"📌 Planta selecionada      : {planta}")
            print(f"📖 Fase atual              : {fase}")
            print(f"⏹️  Estufa em standby. Nenhum controle ativo.")
            print("=" * 85)
            return

        if not inicio_ts:
            return
        inicio_fase = isoparse(inicio_ts).astimezone(timezone.utc)
        dias_corridos = (
            datetime.now(timezone.utc) - inicio_fase
        ).total_seconds() / 86400

        preset = carregar_preset(planta, fase)
        if not preset:
            return
        dias_total = preset.get("DiasNaEtapa", 9999)
        dias_restantes = max(0, dias_total - dias_corridos)

        print(f"\n{'='*20} 🌱  Fase Atual da Estufa  [{hora}] {'='*20}\n")
        print(f"📌 Planta selecionada      : {planta}")
        print(f"📖 Fase atual              : {fase}")
        print(
            f"📅 Duração total da fase   : {dias_total:.4f} dias ({dias_total*1440:.0f} min)"
        )
        print(
            f"⏳ Dias decorridos         : {dias_corridos:.4f} dias ({dias_corridos*1440:.0f} min)"
        )
        print(
            f"⏱️ Dias restantes          : {dias_restantes:.4f} dias ({dias_restantes*1440:.0f} min)"
        )
        print("=" * 85)

    except Exception as e:
        warn(f"Erro ao exibir status da fase: {e}")


def limpar_terminal():
    os.system("cls" if os.name == "nt" else "clear")

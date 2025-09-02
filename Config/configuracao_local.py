from Config.firebase_config import firestore_db
from datetime import datetime, timezone
import json


def carregar_configuracao_local(estufa_id, caminho_arquivo="configuracao_ativa.json"):
    """
    🔧 Carrega o preset da planta/fase atual do Firestore e aplica overrides específicos.
    ✅ Se estiver na fase 'Colheita', não tenta buscar preset e define EstadoSistema = False.
    """
    try:
        # 🔍 Obtém dados gerais da estufa (planta/fase)
        doc_estufa = firestore_db.collection(
            "Dispositivos").document(estufa_id).get()
        if not doc_estufa.exists:
            raise ValueError("Estufa não encontrada no Firestore.")

        dados_estufa = doc_estufa.to_dict()

        planta = dados_estufa.get("PlantaAtual")
        fase = dados_estufa.get("FaseAtual")

        if not planta or not fase:
            raise ValueError(
                "Campos 'PlantaAtual' ou 'FaseAtual' não definidos.")


# 🛑 Se a estufa estiver em Standby, retorna configuração mínima
        if planta == "Standby" or fase == "Standby":
            config_final = {
                "FaseAtual": "Standby",
                "EstadoSistema": False,
                "PlantaAtual": "Standby"
            }
            with open(caminho_arquivo, "w") as f:
                json.dump(config_final, f, indent=4)
            return config_final

        # 🌾 Se a fase for Colheita, não há preset. Retorna config mínima.
        if fase == "Colheita":
            config_final = {
                "FaseAtual": "Colheita",
                "EstadoSistema": False,
                "PlantaAtual": planta,
            }
            with open(caminho_arquivo, "w") as f:
                json.dump(config_final, f, indent=4)
            return config_final

        # 📦 Busca o preset padrão para essa planta/fase
        doc_preset = (
            firestore_db.collection("Presets")
            .document(planta)
            .collection(fase)
            .document("Padrao")
            .get()
        )
        if not doc_preset.exists:
            raise ValueError(
                f"Preset da fase '{fase}' para a planta '{planta}' não encontrado."
            )

        config_final = doc_preset.to_dict()

        # 🛠️ Aplica overrides apenas nos campos desejados
        campos_override = {
            "Temperatura": "TemperaturaDesejada",
            "TemperaturaDoSolo": "TemperaturaDoSoloDesejada",
            "Umidade": "UmidadeDesejada",
            "UmidadeDoSolo": "UmidadeDoSoloDesejada",
            "Luminosidade": "LuminosidadeDesejada",
        }

        for nome_categoria, campo_desejado in campos_override.items():
            if dados_estufa.get(f"Override{nome_categoria}", False):
                doc_override = (
                    firestore_db.collection("Dispositivos")
                    .document(estufa_id)
                    .collection("Dados")
                    .document(nome_categoria)
                    .get()
                )
                if doc_override.exists:
                    valor_desejado = doc_override.get(campo_desejado)
                    if valor_desejado is not None:
                        config_final[campo_desejado] = valor_desejado

        config_final["EstadoSistema"] = dados_estufa.get(
            "EstadoSistema", False)

        # ✅ Inclui campos extras úteis para outras funções
        config_final["PlantaAtual"] = planta
        config_final["FaseAtual"] = fase

        config_final["OverrideTemperatura"] = dados_estufa.get(
            "OverrideTemperatura", False
        )
        config_final["OverrideTemperaturaDoSolo"] = dados_estufa.get(
            "OverrideTemperaturaDoSolo", False
        )
        config_final["OverrideUmidade"] = dados_estufa.get(
            "OverrideUmidade", False)
        config_final["OverrideUmidadeDoSolo"] = dados_estufa.get(
            "OverrideUmidadeDoSolo", False
        )
        config_final["OverrideLuminosidade"] = dados_estufa.get(
            "OverrideLuminosidade", False
        )

        timestamp_raw = dados_estufa.get("InicioFaseTimestamp")
        if isinstance(timestamp_raw, datetime):
            timestamp_utc = timestamp_raw.replace(tzinfo=timezone.utc)
            config_final["InicioFaseTimestamp"] = timestamp_utc.isoformat()
        else:
            config_final["InicioFaseTimestamp"] = None
        config_final["ForcarAvancoFase"] = dados_estufa.get(
            "ForcarAvancoFase", False)

        # 💾 Salva a configuração final localmente
        with open(caminho_arquivo, "w") as f:
            json.dump(config_final, f, indent=4)

        return config_final

    except Exception as e:
        print(f"⚠️ Erro ao carregar configuração da estufa: {e}")
        return None


def carregar_preset(planta, fase):
    """
    Retorna o dicionário do preset da planta/fase.
    Retorna None se não encontrar.
    """
    try:
        doc = (
            firestore_db.collection("Presets")
            .document(planta)
            .collection(fase)
            .document("Padrao")
            .get()
        )
        if doc.exists:
            return doc.to_dict()
        else:
            print(f"⚠️ Preset não encontrado para {planta}/{fase}")
            return None
    except Exception as e:
        print(f"❌ Erro ao carregar preset da fase: {e}")
        return None

# config/configuracao_local.py
from config.firebase_config import firestore_db
import os
from datetime import datetime, timezone
import json


def carregar_configuracao_local(estufa_id, caminho_arquivo=None):
    """
    Carrega a configuração ativa da estufa a partir do Firestore,
    aplicando overrides e salvando localmente em JSON.

    Regras:
      - Standby → retorna config mínima (sem preset, sistema inativo).
      - Colheita → retorna config mínima (sistema inativo).
      - Outras fases → carrega preset padrão + aplica overrides.

    Parâmetros:
        estufa_id (str): Identificador único da estufa.
        caminho_arquivo (str|None): Caminho para salvar o JSON local.
            Se None, usa automaticamente `config/configuracao_ativa.json`.

    Retorna:
        dict | None: configuração final ou None em caso de erro.
    """
    if caminho_arquivo is None:
        caminho_arquivo = os.path.join(
            os.path.dirname(__file__), "configuracao_ativa.json"
        )

    try:
        # 🔍 Busca documento principal da estufa
        doc_estufa = firestore_db.collection("Dispositivos").document(estufa_id).get()
        if not doc_estufa.exists:
            print("🚫 Estufa não encontrada no Firestore.")
            return None

        dados_estufa = doc_estufa.to_dict()
        planta = dados_estufa.get("PlantaAtual")
        fase = dados_estufa.get("FaseAtual")

        if not planta or not fase:
            print("🚫 Campos PlantaAtual ou FaseAtual não definidos.")
            return None

        # 🛑 Standby
        if planta == "Standby" or fase == "Standby":
            config_final = {
                "FaseAtual": "Standby",
                "EstadoSistema": False,
                "PlantaAtual": "Standby",
            }
            _salvar_local(config_final, caminho_arquivo)
            return config_final

        # 🌾 Colheita
        if fase == "Colheita":
            config_final = {
                "FaseAtual": "Colheita",
                "EstadoSistema": False,
                "PlantaAtual": planta,
            }
            _salvar_local(config_final, caminho_arquivo)
            return config_final

        # 📦 Preset da planta/fase
        doc_preset = (
            firestore_db.collection("Presets")
            .document(planta)
            .collection(fase)
            .document("Padrao")
            .get()
        )
        if not doc_preset.exists:
            print(f"🚫 Preset da fase '{fase}' para planta '{planta}' não encontrado.")
            return None

        config_final = doc_preset.to_dict()

        # 🛠️ Overrides aplicáveis
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
                    valor = doc_override.get(campo_desejado)
                    if valor is not None:
                        config_final[campo_desejado] = valor

        # 🔄 Metadados adicionais
        config_final.update(
            {
                "EstadoSistema": dados_estufa.get("EstadoSistema", False),
                "PlantaAtual": planta,
                "FaseAtual": fase,
                "OverrideTemperatura": dados_estufa.get("OverrideTemperatura", False),
                "OverrideTemperaturaDoSolo": dados_estufa.get(
                    "OverrideTemperaturaDoSolo", False
                ),
                "OverrideUmidade": dados_estufa.get("OverrideUmidade", False),
                "OverrideUmidadeDoSolo": dados_estufa.get(
                    "OverrideUmidadeDoSolo", False
                ),
                "OverrideLuminosidade": dados_estufa.get("OverrideLuminosidade", False),
                "ForcarAvancoFase": dados_estufa.get("ForcarAvancoFase", False),
            }
        )

        # ⏱️ Timestamp
        ts_raw = dados_estufa.get("InicioFaseTimestamp")
        if isinstance(ts_raw, datetime):
            config_final["InicioFaseTimestamp"] = ts_raw.replace(
                tzinfo=timezone.utc
            ).isoformat()
        else:
            config_final["InicioFaseTimestamp"] = None

        # 💾 Salva local
        _salvar_local(config_final, caminho_arquivo)

        return config_final

    except Exception as e:
        print(f"⚠️ Erro ao carregar configuração da estufa: {e}")
        return None


def carregar_preset(planta, fase):
    """
    Retorna o dicionário do preset da planta/fase ou None se não existir.

    Parâmetros:
        planta (str): Nome da planta.
        fase (str): Nome da fase ("Germinacao", "Crescimento", etc.).

    Retorna:
        dict | None: configuração padrão da planta/fase ou None se não encontrada.
    """
    try:
        doc = (
            firestore_db.collection("Presets")
            .document(planta)
            .collection(fase)
            .document("Padrao")
            .get()
        )
        return doc.to_dict() if doc.exists else None
    except Exception as e:
        print(f"⚠️ Erro ao carregar preset {planta}/{fase}: {e}")
        return None


def _salvar_local(config, caminho_arquivo):
    """
    Salva a configuração em arquivo JSON local.

    Parâmetros:
        config (dict): configuração da estufa.
        caminho_arquivo (str): caminho para salvar o JSON.
    """
    try:
        with open(caminho_arquivo, "w") as f:
            json.dump(config, f, indent=4)
    except Exception as e:
        print(f"⚠️ Erro ao salvar config local: {e}")

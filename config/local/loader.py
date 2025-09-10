# config/local/loader.py
import os
from datetime import datetime, timezone
from config.firebase.client import firestore_db
from config.paths import LOCAL_CONFIG_PATH
from .preset import carregar_preset
from .saver import salvar_local


def carregar_configuracao_local(
    estufa_id: str, caminho_arquivo: str | None = None
) -> dict | None:
    if caminho_arquivo is None:
        caminho_arquivo = LOCAL_CONFIG_PATH

    try:
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

        # Standby
        if planta == "Standby" or fase == "Standby":
            cfg = {
                "FaseAtual": "Standby",
                "EstadoSistema": False,
                "PlantaAtual": "Standby",
            }
            salvar_local(cfg, caminho_arquivo)
            return cfg

        # Colheita
        if fase == "Colheita":
            cfg = {
                "FaseAtual": "Colheita",
                "EstadoSistema": False,
                "PlantaAtual": planta,
            }
            salvar_local(cfg, caminho_arquivo)
            return cfg

        # Preset base
        cfg = carregar_preset(planta, fase)
        if not cfg:
            print(f"🚫 Preset da fase '{fase}' para planta '{planta}' não encontrado.")
            return None

        # Overrides configuráveis
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
                        cfg[campo_desejado] = valor

        # Metadados adicionais
        cfg.update(
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

        ts_raw = dados_estufa.get("InicioFaseTimestamp")
        if isinstance(ts_raw, datetime):
            cfg["InicioFaseTimestamp"] = ts_raw.replace(tzinfo=timezone.utc).isoformat()
        else:
            cfg["InicioFaseTimestamp"] = None

        salvar_local(cfg, caminho_arquivo)
        return cfg

    except Exception as e:
        print(f"⚠️ Erro ao carregar configuração da estufa: {e}")
        return None

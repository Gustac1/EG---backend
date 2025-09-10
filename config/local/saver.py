# config/local/saver.py
import json


def salvar_local(config: dict, caminho_arquivo: str) -> None:
    try:
        with open(caminho_arquivo, "w") as f:
            json.dump(config, f, indent=4)
    except Exception as e:
        print(f"⚠️ Erro ao salvar config local: {e}")

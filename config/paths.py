# config/paths.py
import os

BASE_DIR = os.path.dirname(__file__)
DEFAULT_CREDENTIALS = os.path.join(
    BASE_DIR, "credentials", "ecogrowth-772d4-firebase-adminsdk-ubo79-eef9fa5c2f.json"
)
LOCAL_CONFIG_PATH = os.path.join(BASE_DIR, "configuracao_ativa.json")


def get_credentials_path() -> str:
    """Prioriza variável de ambiente, senão usa o caminho padrão."""
    return os.getenv("FIREBASE_CREDENTIALS", DEFAULT_CREDENTIALS)


# Permite trocar a URL por env var se precisar, mantendo o valor atual como fallback
DATABASE_URL = os.getenv(
    "FIREBASE_DATABASE_URL", "https://ecogrowth-772d4-default-rtdb.firebaseio.com/"
)

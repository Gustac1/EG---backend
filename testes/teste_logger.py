# testes/teste_logger.py
import time
import csv
import os
from datetime import datetime
from config.configuracao_local import carregar_configuracao_local
from config.firebase_config import realtime_db, firestore_db

BASE_DIR = os.path.dirname(__file__)
CSV_FILE = os.path.join(BASE_DIR, "fixtures", "dados_estufa.csv")

ESTUFA_ID = "EG001"


def inicializar_csv():
    if not os.path.exists(CSV_FILE):
        with open(CSV_FILE, mode="w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(
                [
                    "timestamp",
                    "planta",
                    "fase",
                    "luminosidade",
                    "temp_ar",
                    "umid_ar",
                    "temp_solo",
                    "umid_solo",
                    "aquecedor_estado",
                    "aquecedor_motivo",
                    "ventoinha_estado",
                    "ventoinha_motivo",
                    "luminaria_estado",
                    "luminaria_motivo",
                    "bomba_estado",
                    "bomba_motivo",
                ]
            )


def teste_logger():
    inicializar_csv()
    print("📝 Logger CSV iniciado (Realtime + Firestore).")

    while True:
        try:
            # 🔹 Config da estufa (fase/planta)
            config = carregar_configuracao_local(ESTUFA_ID)
            if not config:
                time.sleep(30)
                continue

            # 🔹 Sensores → Realtime DB
            snapshot = realtime_db.child(f"Dispositivos/{ESTUFA_ID}/DadosAtuais").get()
            if not snapshot:
                print("⚠️ Nenhum dado encontrado no Realtime DB.")
                time.sleep(10)
                continue

            sensores = {
                "LuminosidadeAtual": snapshot.get("LuminosidadeAtual"),
                "TemperaturaDoArAtual": snapshot.get("TemperaturaDoArAtual"),
                "UmidadeDoArAtual": snapshot.get("UmidadeDoArAtual"),
                "TemperaturaDoSoloAtual": snapshot.get("TemperaturaDoSoloAtual"),
                "UmidadeDoSoloAtual": snapshot.get("UmidadeDoSoloAtual"),
            }

            # 🔹 Atuadores → Firestore
            docs = (
                firestore_db.collection("Dispositivos")
                .document(ESTUFA_ID)
                .collection("Dados")
                .get()
            )
            atuadores = {
                "Aquecedor": (None, None),
                "Ventoinha": (None, None),
                "Luminaria": (None, None),
                "Bomba": (None, None),
            }
            for d in docs:
                nome = d.id
                dados = d.to_dict()
                if nome in atuadores:
                    atuadores[nome] = (dados.get("Estado"), dados.get("Motivo"))

            # 🔹 Escreve no CSV
            with open(CSV_FILE, mode="a", newline="") as f:
                writer = csv.writer(f)
                writer.writerow(
                    [
                        datetime.now().isoformat(),
                        config.get("PlantaAtual"),
                        config.get("FaseAtual"),
                        sensores["LuminosidadeAtual"],
                        sensores["TemperaturaDoArAtual"],
                        sensores["UmidadeDoArAtual"],
                        sensores["TemperaturaDoSoloAtual"],
                        sensores["UmidadeDoSoloAtual"],
                        atuadores["Aquecedor"][0],
                        atuadores["Aquecedor"][1],
                        atuadores["Ventoinha"][0],
                        atuadores["Ventoinha"][1],
                        atuadores["Luminaria"][0],
                        atuadores["Luminaria"][1],
                        atuadores["Bomba"][0],
                        atuadores["Bomba"][1],
                    ]
                )

            time.sleep(30)

        except Exception as e:
            print(f"⚠️ Erro no teste_logger: {e}")
            time.sleep(30)

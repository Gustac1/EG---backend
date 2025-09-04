# Services/controle_service.py
import time
from Utils.logger import warn
from Config.firebase_config import atualizar_status_atuador
from Config.configuracao_local import carregar_configuracao_local


def controlar_atuadores(
    ventoinha,
    luminaria,
    bomba,
    aquecedor,
    temperatura_ar,
    umidade_ar,
    umidade_solo,
    config,
):
    """
    Decide o estado dos atuadores (ligado/desligado) com base na configuração
    da estufa e nas leituras atuais de sensores.

    A função NÃO envia dados ao Firebase nem imprime status no terminal.
    Apenas retorna um dicionário com os estados e motivos de cada atuador.
    Em caso de erro ou ausência de configuração, todos os atuadores são desligados
    por segurança.

    Parâmetros:
        ventoinha (obj): objeto da classe Ventoinha com métodos ligar()/desligar()/controlar().
        luminaria (obj): objeto da classe Luminaria com métodos ligar()/desligar()/controlar().
        bomba (obj): objeto da classe Bomba com métodos ligar()/desligar()/controlar().
        aquecedor (obj): objeto da classe Aquecedor com métodos ligar()/desligar()/controlar().
        temperatura_ar (float|None): temperatura do ar atual (°C).
        umidade_ar (float|None): umidade relativa do ar atual (%).
        umidade_solo (float|None): umidade do solo atual (% ou unidade do sensor).
        config (dict): configuração ativa da estufa (carregada de arquivo ou Firestore).

    Retorna:
        dict: dicionário com o estado e motivo de cada atuador.
        Exemplo:
            {
                "Aquecedor": (True, "Temperatura abaixo do limite"),
                "Ventoinha": (False, "Umidade adequada"),
                "Luminária": (True, "Fotoperíodo ativo"),
                "Bomba": (False, "Solo úmido o suficiente"),
            }

        Em caso de erro ou ausência de configuração:
            {
                "Aquecedor": (False, "Erro no controle"),
                "Ventoinha": (False, "Erro no controle"),
                "Luminária": (False, "Erro no controle"),
                "Bomba": (False, "Erro no controle"),
            }

    Casos especiais:
        - FaseAtual = "Standby" → todos os atuadores desligados, motivo "Estufa em Standby".
        - FaseAtual = "Colheita" → todos desligados, motivo "Fase Colheita".
        - EstadoSistema = False → todos desligados, motivo "Sistema desativado".
        - Fases normais → decisão feita pelas lógicas individuais de cada atuador.

    Segurança:
        - Qualquer exceção capturada resulta em desligamento de todos os atuadores,
          com motivo "Erro no controle".
    """
    try:
        if not config:
            print("[ERRO] Configuração local não encontrada.")
            return {
                "Aquecedor": (False, "Erro no controle"),
                "Ventoinha": (False, "Erro no controle"),
                "Luminaria": (False, "Erro no controle"),
                "Bomba": (False, "Erro no controle"),
            }

        # --- Standby ---
        if config.get("FaseAtual") == "Standby":
            motivo = "Estufa em Standby"
            ventoinha.desligar()
            luminaria.desligar()
            bomba.desligar()
            aquecedor.desligar()

            status_atuadores = {
                "Aquecedor": (False, motivo),
                "Ventoinha": (False, motivo),
                "Luminaria": (False, motivo),
                "Bomba": (False, motivo),
            }

        # --- Colheita ou sistema parado ---
        elif config.get("FaseAtual") == "Colheita" or not config.get(
            "EstadoSistema", False
        ):
            motivo = (
                "Fase Colheita"
                if config.get("FaseAtual") == "Colheita"
                else "Sistema desativado"
            )
            ventoinha.desligar()
            luminaria.desligar()
            bomba.desligar()
            aquecedor.desligar()

            status_atuadores = {
                "Aquecedor": (False, motivo),
                "Ventoinha": (False, motivo),
                "Luminaria": (False, motivo),
                "Bomba": (False, motivo),
            }

        # --- Operação normal ---
        else:

            aquecedor_ativo, motivo_aquecedor = aquecedor.controlar(
                temperatura_ar, config
            )

            ventoinha_ativa, motivo_ventoinha = ventoinha.controlar(
                temperatura_ar, umidade_ar, aquecedor_ativo, config
            )

            luminaria_ativa, motivo_luminaria = luminaria.controlar(config=config)

            bomba_ativa, motivo_bomba = bomba.controlar(umidade_solo, config)

            status_atuadores = {
                "Aquecedor": (aquecedor_ativo, motivo_aquecedor),
                "Ventoinha": (ventoinha_ativa, motivo_ventoinha),
                "Luminaria": (luminaria_ativa, motivo_luminaria),
                "Bomba": (bomba_ativa, motivo_bomba),
            }

        return status_atuadores

    except Exception as e:
        print(f"[ERRO] Falha ao controlar atuadores: {e}")
        return {
            "Aquecedor": (False, "Erro no controle"),
            "Ventoinha": (False, "Erro no controle"),
            "Luminaria": (False, "Erro no controle"),
            "Bomba": (False, "Erro no controle"),
        }


def rodar_controle_once(
    estufa_id,
    ventoinha,
    luminaria,
    bomba,
    aquecedor,
    temperatura_ar_sensor,
    umidade_solo_sensor,
    exibir_status_atuadores=None,
    exibir_status_fase=None,
):
    """Executa uma rodada única do controle de atuadores (sem loop infinito)."""
    try:
        config = carregar_configuracao_local(estufa_id)
        if not config:
            warn("⚠️ Erro ao carregar configuração local.")
            return

        temperatura_ar, umidade_ar = temperatura_ar_sensor.ler_dados()
        umidade_solo = umidade_solo_sensor.ler_umidade()

        # --- Aquecedor ---
        aquecedor_ativo, motivo_aquecedor = aquecedor.controlar(temperatura_ar, config)
        atualizar_status_atuador(
            estufa_id, "Aquecedor", aquecedor_ativo, motivo_aquecedor
        )

        # --- Ventoinha ---
        ventoinha_ativa, motivo_ventoinha = ventoinha.controlar(
            temperatura_ar, umidade_ar, aquecedor_ativo, config
        )
        atualizar_status_atuador(
            estufa_id, "Ventoinha", ventoinha_ativa, motivo_ventoinha
        )

        # --- Luminária ---
        luminaria_ativa, motivo_luminaria = luminaria.controlar(config=config)
        atualizar_status_atuador(
            estufa_id, "Luminaria", luminaria_ativa, motivo_luminaria
        )

        # --- Bomba ---
        bomba_ativa, motivo_bomba = bomba.controlar(umidade_solo, config)
        atualizar_status_atuador(estufa_id, "Bomba", bomba_ativa, motivo_bomba)

        # --- Exibição no terminal ---
        status_atuadores = {
            "Aquecedor": (aquecedor_ativo, motivo_aquecedor),
            "Ventoinha": (ventoinha_ativa, motivo_ventoinha),
            "Luminaria": (luminaria_ativa, motivo_luminaria),
            "Bomba": (bomba_ativa, motivo_bomba),
        }
        if exibir_status_atuadores:
            exibir_status_atuadores(status_atuadores)
        if exibir_status_fase:
            exibir_status_fase(config)

    except Exception as e:
        warn(f"Erro em rodada única de controle: {e}")


def desligar_todos_atuadores(
    estufa_id,
    ventoinha,
    luminaria,
    bomba,
    aquecedor,
    exibir_status_atuadores=None,
    exibir_status_fase=None,
):
    """
    Desliga imediatamente todos os atuadores e atualiza o status no Firestore.
    Usado em eventos de reinício/reset.
    """
    try:
        motivo = "Estufa em Standby"

        ventoinha.desligar()
        luminaria.desligar()
        bomba.desligar()
        aquecedor.desligar()

        status_atuadores = {
            "Aquecedor": (False, motivo),
            "Ventoinha": (False, motivo),
            "Luminaria": (False, motivo),
            "Bomba": (False, motivo),
        }

        atualizar_status_atuador(estufa_id, "Aquecedor", False, motivo)
        atualizar_status_atuador(estufa_id, "Ventoinha", False, motivo)
        atualizar_status_atuador(estufa_id, "Luminaria", False, motivo)
        atualizar_status_atuador(estufa_id, "Bomba", False, motivo)

        if exibir_status_atuadores:
            exibir_status_atuadores(status_atuadores)

        # carrega a config atualizada em standby e mostra no terminal
        from Config.configuracao_local import carregar_configuracao_local

        config = carregar_configuracao_local(estufa_id)
        if exibir_status_fase and config:
            exibir_status_fase(config)

    except Exception as e:
        warn(f"Erro ao desligar atuadores no reinício: {e}")

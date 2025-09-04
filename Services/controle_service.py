# Services/controle_service.py


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

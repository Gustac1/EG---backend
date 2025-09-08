# services/coleta_service.py
import time

# Buffer global para o histórico (compartilhado com envio periódico).
# Cada chave representa um tipo de sensor e armazena uma lista com as últimas leituras.
# Esse buffer é consumido depois pelo envio periódico (envio_service) para calcular médias.
buffer_sensores = {
    "Luminosidade": [],
    "TemperaturaDoSolo": [],
    "Temperatura": [],
    "Umidade": [],
    "UmidadeDoSolo": [],
}


def tentar_ler(func, tentativas=5):
    """
    Executa a função de leitura de sensor até N tentativas.

    Parâmetros:
        func (callable): referência para a função de leitura do sensor,
                         passada sem parênteses.
                         Exemplo:
                            tentar_ler(sensor.ler_umidade)
                            tentar_ler(sensor.read_temp)

        tentativas (int): número máximo de chamadas à função (default=5).

    Retorna:
        - Valor retornado pela função (float, tupla ou outro tipo esperado),
          se em alguma tentativa não for None.
        - None, se todas as tentativas retornarem None ou gerarem erro.

    Observações:
        - Útil para lidar com leituras instáveis (ex.: DHT22).
        - Cada chamada é protegida com try/except para evitar crash.
    """
    for _ in range(tentativas):
        try:
            valor = func()
            if valor is not None:
                return valor
        except Exception:
            pass
    return None


def arredondar(valor, casas=2):
    """
    Arredonda um valor numérico para o número de casas decimais especificado.

    Parâmetros:
        valor (float|None): número a ser arredondado.
        casas (int): número de casas decimais (default=2).

    Retorna:
        - Valor arredondado (float) se for numérico.
        - None, se o valor original for None.

    Exemplos:
        arredondar(25.6789) → 25.68
        arredondar(None)    → None
    """
    return round(valor, casas) if valor is not None else None


def coletar_dados(
    luminosidade_sensor,
    temperatura_solo_sensor,
    temperatura_ar_sensor,
    umidade_solo_sensor,
):
    """
    Executa uma rodada única de coleta de dados dos sensores da estufa.

    Fluxo:
        1. Lê cada sensor individualmente:
            - Luminosidade (BH1750)
            - Temperatura do solo (DS18B20)
            - Temperatura e umidade do ar (DHT22)
            - Umidade do solo (sensor capacitivo)
        2. Aplica arredondamento e validações.
        3. Monta um dicionário `dados_atuais` com os valores.
        4. Atualiza o buffer_sensores com valores válidos (não-None).
        5. Retorna o dicionário com as leituras da rodada.

    Parâmetros:
        luminosidade_sensor (obj): instância do sensor BH1750.
        temperatura_solo_sensor (obj): instância do sensor DS18B20.
        temperatura_ar_sensor (obj): instância do sensor DHT22.
        umidade_solo_sensor (obj): instância do sensor de umidade do solo.

    Retorna:
        dict: com os valores atuais de cada sensor + timestamp.
            Exemplo:
            {
                "LuminosidadeAtual": 234.56,
                "TemperaturaDoArAtual": 25.4,
                "UmidadeDoArAtual": 60.1,
                "TemperaturaDoSoloAtual": 23.9,
                "UmidadeDoSoloAtual": 41.7,
                "timestamp": 1725405678.12
            }
        None: em caso de erro inesperado.
    """
    try:
        # Luminosidade
        lux = arredondar(tentar_ler(luminosidade_sensor.ler_luminosidade))

        # Temperatura do solo
        temperatura_solo = arredondar(tentar_ler(temperatura_solo_sensor.read_temp))

        # Temperatura e umidade do ar (DHT22)
        (temperatura_ar, umidade_ar) = tentar_ler(temperatura_ar_sensor.ler_dados)
        temperatura_ar = arredondar(temperatura_ar)
        umidade_ar = arredondar(umidade_ar)

        # Umidade do solo
        umidade_solo = arredondar(tentar_ler(umidade_solo_sensor.ler_umidade))

        # Dicionário com as leituras atuais
        dados_atuais = {
            "LuminosidadeAtual": lux,
            "TemperaturaDoArAtual": temperatura_ar,
            "UmidadeDoArAtual": umidade_ar,
            "TemperaturaDoSoloAtual": temperatura_solo,
            "UmidadeDoSoloAtual": umidade_solo,
            "timestamp": round(time.time(), 2),
        }

        # Preenchimento do buffer histórico (apenas valores válidos)
        if lux is not None:
            buffer_sensores["Luminosidade"].append(lux)
        if temperatura_solo is not None:
            buffer_sensores["TemperaturaDoSolo"].append(temperatura_solo)
        if temperatura_ar is not None:
            buffer_sensores["Temperatura"].append(temperatura_ar)
        if umidade_ar is not None:
            buffer_sensores["Umidade"].append(umidade_ar)
        if umidade_solo is not None:
            buffer_sensores["UmidadeDoSolo"].append(umidade_solo)

        return dados_atuais

    except Exception as e:
        print(f"⚠️ Erro ao coletar dados dos sensores: {e}")
        return None

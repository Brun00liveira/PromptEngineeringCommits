# Chatbot de previsão do tempo no terminal, falando direto com a API do Ollama (sem pacotes),
# com uma ferramenta (tool) que consulta a previsão real na API gratuita Open-Meteo.

import json
import urllib.request
import urllib.error
import urllib.parse    # monta a parte "?nome=valor&..." da URL (como URLSearchParams no JS)
from datetime import date  # para converter as datas da API e saber o dia da semana

URL_OLLAMA = "http://localhost:11434/api/chat"
URL_GEOCODING = "https://geocoding-api.open-meteo.com/v1/search"  # nome da cidade -> latitude/longitude
URL_PREVISAO = "https://api.open-meteo.com/v1/forecast"           # latitude/longitude -> previsão
MODELO = "qwen3.5"

# Aspas triplas: texto de várias linhas. As quebras de linha fazem parte do texto,
# então o modelo enxerga as seções do prompt.
INSTRUCOES = """
# Papel
Você é um assistente de previsão do tempo. Você consulta a previsão com uma
ferramenta e explica o resultado de forma simples, sempre em português do Brasil.

# Contexto
- Você não sabe como está o tempo em nenhuma cidade ou país.
- Os dados de previsão vêm da ferramenta consultar_previsao.
- A maioria dos usuários mora em Lorena/SP e região.

# Regras
- Sempre que perguntarem sobre tempo, clima, temperatura ou chuva, use a
  ferramenta consultar_previsao e responda apenas com o que ela devolver.
  Nunca invente dados.
- Se não disserem o lugar, considere Lorena/SP.
- Se a ferramenta der erro ou não encontrar a cidade, diga isso ao usuário
  e peça para ele conferir o nome.
- Se perguntarem algo que não seja sobre o tempo, diga educadamente que você
  só ajuda com previsão do tempo.

# Formato da resposta
- Se perguntarem sobre um dia específico (ex.: "vai chover amanhã?"),
  responda só sobre aquele dia, em até 2 frases.
- Se pedirem a previsão geral ou da semana, mostre os próximos 7 dias,
  um por linha, neste formato:
  Seg 20/10: máx. 28°C, mín. 17°C, chuva 40%
- Use sempre °C para temperatura e % para chance de chuva.
- Não use emojis.
"""

FERRAMENTAS = [
    {
        "type": "function",
        "function": {
            "name": "consultar_previsao",
            "description": "Consulta a previsão do tempo dos próximos 7 dias de uma cidade: "
                           "temperatura máxima, mínima e chance de chuva de cada dia.",
            "parameters": {
                "type": "object",
                "properties": {
                    "cidade": {
                        "type": "string",
                        "description": "Só o nome da cidade, sem estado nem país. Ex.: Lorena, Tóquio, Lisboa",
                    },
                    "pais": {
                        "type": "string",
                        "description": "Código do país com 2 letras, se souber. Ex.: BR, JP, PT",
                    },
                },
                "required": ["cidade"],  # "pais" é opcional
            },
        },
    },
]

# Lista de nomes: o índice 0 é segunda-feira, igual ao date.weekday() do Python
DIAS_SEMANA = ["Seg", "Ter", "Qua", "Qui", "Sex", "Sáb", "Dom"]


def chamar_ollama(mensagens):
    dados = {
        "model": MODELO,
        "messages": mensagens,
        "tools": FERRAMENTAS,
        "stream": False,
        "think": False,
    }
    requisicao = urllib.request.Request(
        URL_OLLAMA,
        data=json.dumps(dados).encode("utf-8"),
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(requisicao) as resposta:
        return json.loads(resposta.read())["message"]


# Função auxiliar: faz um GET e já devolve o JSON convertido em dict
def buscar_json(url, parametros):
    endereco = url + "?" + urllib.parse.urlencode(parametros)
    with urllib.request.urlopen(endereco, timeout=15) as resposta:
        return json.loads(resposta.read())


# A ferramenta de verdade. Ela faz duas consultas:
# 1) descobre a latitude/longitude da cidade; 2) busca a previsão nessas coordenadas.
# "pais=None" é um parâmetro com valor padrão: se o modelo não mandar, vale None.
def consultar_previsao(cidade, pais=None):
    try:
        parametros = {"name": cidade, "count": 1, "language": "pt", "format": "json"}
        if pais:
            parametros["countryCode"] = pais
        local = buscar_json(URL_GEOCODING, parametros)

        # Se a cidade não existir, a API devolve um JSON sem a chave "results"
        if not local.get("results"):
            return f"Erro: cidade '{cidade}' não encontrada."
        lugar = local["results"][0]  # pega o primeiro resultado

        previsao = buscar_json(URL_PREVISAO, {
            "latitude": lugar["latitude"],
            "longitude": lugar["longitude"],
            "daily": "temperature_2m_max,temperature_2m_min,precipitation_probability_max",
            "timezone": "auto",
            "forecast_days": 7,
        })
    except urllib.error.URLError:
        return "Erro: não foi possível consultar a previsão agora."

    diario = previsao["daily"]
    # O primeiro dia da previsão é "hoje" no fuso da cidade (em Tóquio pode já ser amanhã aqui)
    hoje = date.fromisoformat(diario["time"][0])

    # Monta o texto que o modelo vai ler, um dia por linha.
    # zip() percorre várias listas ao mesmo tempo, como se fossem colunas de uma tabela.
    linhas = [f"Previsão para {lugar['name']}, {lugar.get('admin1', '')}, {lugar.get('country', '')}:"]
    for dia, maxima, minima, chuva in zip(
        diario["time"],
        diario["temperature_2m_max"],
        diario["temperature_2m_min"],
        diario["precipitation_probability_max"],
    ):
        data = date.fromisoformat(dia)  # "2026-10-14" -> objeto date
        # Diz ao modelo qual linha é "hoje" e "amanhã", porque ele não sabe a data atual
        rotulo = {0: " (hoje)", 1: " (amanhã)"}.get((data - hoje).days, "")
        linhas.append(
            f"{DIAS_SEMANA[data.weekday()]} {data:%d/%m}{rotulo}: "
            f"máx. {maxima:.0f}°C, mín. {minima:.0f}°C, chuva {chuva}%"
        )
    return "\n".join(linhas)  # junta as linhas com quebra de linha (como .join("\n") no JS)


print("Previsão do tempo com Ollama. Digite 'sair' para encerrar.\n")

# A lista é criada UMA vez, fora do loop: assim o bot lembra da conversa inteira.
mensagens = [{"role": "system", "content": INSTRUCOES}]

while True:
    pergunta = input("Você: ")

    if pergunta.strip().lower() == "sair":
        break

    mensagens.append({"role": "user", "content": pergunta})
    resposta = chamar_ollama(mensagens)

    while resposta.get("tool_calls"):
        mensagens.append(resposta)

        for chamada in resposta["tool_calls"]:
            nome = chamada["function"]["name"]
            argumentos = chamada["function"]["arguments"]

            if nome == "consultar_previsao":
                # **argumentos "desempacota" o dict em parâmetros nomeados:
                # {"cidade": "Lorena", "pais": "BR"} vira consultar_previsao(cidade="Lorena", pais="BR")
                resultado = consultar_previsao(**argumentos)
            else:
                resultado = f"Erro: ferramenta '{nome}' não existe."

            print(f"  [ferramenta] {nome}({argumentos})")

            mensagens.append({"role": "tool", "tool_name": nome, "content": resultado})

        resposta = chamar_ollama(mensagens)

    mensagens.append(resposta)  # guarda a resposta do bot no histórico também
    print(f"Bot: {resposta['content']}\n")

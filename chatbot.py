# Chatbot no terminal, falando direto com a API do Ollama (sem pacotes),
# com uma ferramenta (tool) que consulta a hora real de qualquer país numa API externa.

# "import" carrega módulos que já vêm com o Python (como "require"/"import" no Node)
import json            # converter dicionário <-> texto JSON (como JSON.stringify / JSON.parse)
import urllib.request  # fazer requisições HTTP (como fetch no Node ou Http:: no Laravel)
import urllib.error    # os tipos de erro que o urllib pode dar (ex.: 400, 404)

# Variáveis: não precisa de "let", "const" nem "$". Basta nome = valor.
# Nomes em MAIÚSCULAS são uma convenção para "constante" (o Python não impede de mudar).
URL_OLLAMA = "http://localhost:11434/api/chat"
URL_HORARIO = "https://timeapi.io/api/time/current/zone?timeZone="
MODELO = "qwen3.5"

INSTRUCOES = (
    "Você é um assistente que responde sempre em português do Brasil. "
    "Você NÃO sabe a data nem a hora atual. Sempre que perguntarem sobre data ou hora, "
    "use a ferramenta consultar_horario e responda com o que ela devolver. Nunca invente. "
    "Se não disserem o lugar, considere o Brasil (America/Sao_Paulo)."
)

# Descrição da ferramenta, no formato que o Ollama espera.
# O modelo NÃO executa nada: ele só lê isto e decide "quero chamar essa função com tal argumento".
FERRAMENTAS = [
    {
        "type": "function",
        "function": {
            "name": "consultar_horario",
            "description": "Consulta a data e a hora atuais de um fuso horário.",
            "parameters": {
                "type": "object",
                "properties": {
                    "fuso_horario": {
                        "type": "string",
                        "description": "Fuso no padrão IANA, ex.: America/Sao_Paulo, Asia/Tokyo, Europe/Lisbon",
                    },
                },
                "required": ["fuso_horario"],
            },
        },
    },
]


# "def" cria uma função (como "function" no JS/PHP). O que vem depois de "return" é o resultado.
def chamar_ollama(mensagens):
    dados = {
        "model": MODELO,
        "messages": mensagens,
        "tools": FERRAMENTAS,
        "stream": False,  # resposta inteira de uma vez (streaming fica para depois)
        "think": False,   # o qwen3.5 "pensa" antes de responder; desligado fica mais rápido
    }
    # json.dumps: dict -> texto JSON; .encode("utf-8"): texto -> bytes, que é o que vai pela rede
    requisicao = urllib.request.Request(
        URL_OLLAMA,
        data=json.dumps(dados).encode("utf-8"),
        headers={"Content-Type": "application/json"},
    )
    # "with" abre a conexão e garante que ela seja fechada no fim do bloco
    with urllib.request.urlopen(requisicao) as resposta:
        return json.loads(resposta.read())["message"]  # texto JSON -> dict


# A ferramenta de verdade: quem executa é o NOSSO código, não o modelo.
def consultar_horario(fuso_horario):
    # try/except = try/catch do JS/PHP
    try:
        with urllib.request.urlopen(URL_HORARIO + fuso_horario, timeout=15) as resposta:
            return resposta.read().decode("utf-8")  # devolve o JSON da API como texto
    except urllib.error.HTTPError:
        # Fuso inválido: avisamos o modelo, e ele pode tentar de novo com outro nome
        return f"Erro: fuso horário '{fuso_horario}' não existe."


print("Chatbot com Ollama. Digite 'sair' para encerrar.\n")

# "while True:" = loop infinito. Os dois-pontos abrem um bloco,
# e o que está DENTRO do bloco é definido pela indentação (4 espaços), não por { }.
while True:
    pergunta = input("Você: ")  # espera você digitar + Enter

    if pergunta.strip().lower() == "sair":
        break  # sai do while

    # Lista (list) de dicionários (dict). Lista = array do JS; dict = objeto do JS.
    mensagens = [
        {"role": "system", "content": INSTRUCOES},
        {"role": "user", "content": pergunta},
    ]

    resposta = chamar_ollama(mensagens)

    # Enquanto o modelo pedir ferramentas, a gente executa e devolve o resultado para ele.
    # .get("tool_calls") devolve None (o "null" do Python) se a chave não existir, em vez de dar erro.
    while resposta.get("tool_calls"):
        mensagens.append(resposta)  # .append = .push do JS: guarda o pedido do modelo no histórico

        # "for x in lista:" percorre a lista (como "for (const x of lista)" no JS)
        for chamada in resposta["tool_calls"]:
            nome = chamada["function"]["name"]
            argumentos = chamada["function"]["arguments"]

            if nome == "consultar_horario":
                resultado = consultar_horario(argumentos["fuso_horario"])
            else:
                resultado = f"Erro: ferramenta '{nome}' não existe."

            print(f"  [ferramenta] {nome}({argumentos}) -> {resultado}")

            # Devolve o resultado com role "tool", para o modelo usar na resposta
            mensagens.append({"role": "tool", "tool_name": nome, "content": resultado})

        resposta = chamar_ollama(mensagens)  # pergunta de novo, agora com o resultado em mãos

    # f-string: o f antes das aspas permite colocar variáveis dentro de { }
    print(f"Bot: {resposta['content']}\n")

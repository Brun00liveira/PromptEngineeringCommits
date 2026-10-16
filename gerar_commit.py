# Gera uma sugestão de mensagem de commit a partir do "git diff --staged",
# usando o prompt de prompts/commit.md e o modelo local do Ollama.
# Uso: faça "git add" nos arquivos e rode "python gerar_commit.py" dentro do repositório.

import json            # converter dicionário <-> texto JSON
import subprocess      # rodar comandos do terminal (aqui, o git) de dentro do Python
import sys             # acesso à saída do terminal
import urllib.request  # fazer requisições HTTP para o Ollama
import urllib.error    # erros de conexão (ex.: Ollama desligado)
from pathlib import Path  # montar caminhos de arquivo sem depender da pasta atual

URL_OLLAMA = "http://localhost:11434/api/chat"
MODELO = "qwen3.5"

# O Ollama usa 4.096 tokens de contexto por padrão. Em código, 1 token ~ 3 a 4 caracteres,
# então 12.000 caracteres de diff (~3.000 tokens) deixam espaço para o prompt e a resposta.
LIMITE_DIFF = 12000
LIMITE_TITULO = 72

# Path(__file__).parent = pasta onde este script está. Assim o prompt é achado
# mesmo que você rode o script a partir de outra pasta.
CAMINHO_PROMPT = Path(__file__).parent / "prompts" / "commit.md"


def pegar_diff():
    resultado = subprocess.run(
        ["git", "diff", "--staged"],
        capture_output=True, text=True, encoding="utf-8",
    )
    # returncode diferente de 0 = o git reclamou (ex.: pasta que não é repositório)
    if resultado.returncode != 0:
        raise SystemExit("Erro do git: " + resultado.stderr.strip())
    return resultado.stdout


def chamar_ollama(mensagens):
    dados = {
        "model": MODELO,
        "messages": mensagens,
        "stream": False,
        "think": False,
        "options": {"temperature": 0.2},  # mais baixo = respostas mais previsíveis
    }
    requisicao = urllib.request.Request(
        URL_OLLAMA,
        data=json.dumps(dados).encode("utf-8"),
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(requisicao) as resposta:
        return json.loads(resposta.read())["message"]["content"]


def main():
    # O terminal do Windows nem sempre usa UTF-8; sem isso os acentos saem quebrados.
    sys.stdout.reconfigure(encoding="utf-8")

    diff = pegar_diff()

    # Sem nada no stage, o modelo inventaria um commit. Melhor parar aqui.
    if not diff.strip():
        print("Nada no stage. Rode 'git add <arquivos>' antes.")
        return

    # Diff grande: corta e avisa, para não estourar a janela de contexto do modelo.
    if len(diff) > LIMITE_DIFF:
        print(f"Aviso: o diff tem {len(diff)} caracteres; usando só os primeiros {LIMITE_DIFF}.")
        print("A mensagem pode não cobrir todas as mudanças. Considere commits menores.\n")
        diff = diff[:LIMITE_DIFF]

    instrucoes = CAMINHO_PROMPT.read_text(encoding="utf-8")
    mensagens = [
        {"role": "system", "content": instrucoes},
        {"role": "user", "content": diff},
    ]

    try:
        mensagem = chamar_ollama(mensagens).strip()
    except urllib.error.URLError:
        raise SystemExit("Não consegui falar com o Ollama. Ele está rodando? (ollama serve)")

    print(mensagem)

    # Critério do exercício: título com no máximo 72 caracteres, conferido no código.
    titulo = mensagem.splitlines()[0] if mensagem else ""
    if len(titulo) > LIMITE_TITULO:
        print(f"\nAviso: o título tem {len(titulo)} caracteres (máximo {LIMITE_TITULO}).")


# Só roda o main() quando o arquivo é executado direto (não quando é importado)
if __name__ == "__main__":
    main()

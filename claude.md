# Contexto do projeto: estudo de AI Engineer com Ollama

Este arquivo resume uma conversa anterior no claude.ai para dar contexto a esta sessão.

## Quem sou e o que estou fazendo

- Estou estudando o roadmap de AI Engineer (https://roadmap.sh/ai-engineer).
- Sou iniciante em IA. **Não sei Python** e quero aprender a linguagem com este projeto.
  Já conheço Node.js e Laravel (PHP).
- Prefiro explicações em português do Brasil, passo a passo, com o porquê de cada coisa.
- Estou montando um relatório de estudos chamado "Ollama — Resumo de estudos" (Claude Doc no claude.ai).

## Meu ambiente

- Windows, usando **PowerShell** (atenção: `curl` no PowerShell não funciona como no Linux;
  usar `Invoke-RestMethod` ou `curl.exe`).
- 32 GB de RAM.
- GPU: **AMD Radeon RX 7600 com 8 GB de VRAM** (o Ollama detecta via ROCm).
  Modelos de até ~7 GB rodam inteiros na GPU; maiores dividem com a CPU e ficam lentos.
- **Ollama 0.40.4** instalado. Servidor em `http://localhost:11434`.
- Modelo baixado: `llama3.1` (8B, ~4.7 GB). Ao rodar `ollama serve`, o log mostrou
  `total blobs: 0`, então vale conferir com `ollama list` se o modelo está mesmo instalado.
- Contexto padrão do Ollama na minha máquina: 4.096 tokens (`default_num_ctx=4096`).
- Python: **ainda não instalado** (instalar com `winget install Python.Python.3.12`,
  marcando "Add Python to PATH" se for pelo instalador).

## O que já aprendi

- Ollama é o programa que roda modelos; Llama é um modelo da Meta (Ollama = Spotify, modelos = músicas).
- Rodar localmente é grátis e sem limite. O Ollama Cloud (modelos com `:cloud`) tem cota
  gratuita limitada, que renova por sessão (5h) e por semana.
- Digitar só `ollama` abre um menu de integrações (Claude Code, OpenCode etc.).
  Comandos úteis: `ollama run`, `pull`, `list`, `ps`, `stop`, `rm`, `show`, `help`, flag `--verbose`.
- Nome de modelo = `modelo:tamanho` (ex.: `gemma4:12b`). O "Size" é o espaço em disco,
  e é preciso ter mais ou menos isso livre de memória para rodar.
- Etiquetas da biblioteca: `tools`, `thinking`, `vision`, `embedding`, `cloud`.
- Testei o llama3.1 e ele **alucinou**: inventou o horário de São Paulo e errou a própria
  data de corte. Solução futura: dar uma ferramenta (tool) ao modelo ou usar RAG.
- A API do Ollama tem endpoints próprios (`/api/chat`, `/api/generate`, `/api/embed`, `/api/tags`)
  e também é **compatível com a Messages API da Anthropic** (`/v1/messages`): dá para usar o
  SDK `anthropic` com `base_url='http://localhost:11434'` e `api_key='ollama'` (ignorada).
- Qualquer linguagem que faz HTTP funciona (Node, Laravel...), mas o roadmap usa mais Python.

## O que já foi feito

- Um chatbot em Node (`chatbot.mjs`) com memória (histórico) e streaming, usando a biblioteca `ollama`.

## Próximo passo (o que quero fazer agora)

Fazer o **mesmo chatbot em Python**, aprendendo a linguagem no caminho:

1. Instalar o Python e a biblioteca (`pip install ollama`).
2. Chatbot simples no terminal.
3. Adicionar memória (lista de mensagens enviada a cada pergunta).
4. Adicionar streaming e uma mensagem `system` pedindo respostas em português.

Projetos seguintes planejados: RAG que responde perguntas sobre PDFs; agente com ferramentas
(por exemplo, uma tool que lê o relógio do computador para corrigir a alucinação do horário).

## Como quero que você me ajude

- Explique cada conceito novo de Python quando ele aparecer (variáveis, listas, dicionários, loops, imports).
- Faça em passos pequenos e me deixe rodar cada etapa antes de seguir.
- Ao final de cada etapa, resuma o que aprendi para eu colocar no meu relatório.

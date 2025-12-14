# 🐦 Twitter Distribuído: Consistência Eventual vs. Causal

Este projeto é uma implementação acadêmica de um sistema de mensagens distribuído (simulando um Twitter simplificado) para demonstrar na prática as diferenças entre **Consistência Eventual** e **Consistência Causal**.

O objetivo é evidenciar como diferentes modelos lidam com a latência de rede e a ordem de entrega de mensagens (Posts e Replies).

---

## 📋 Sobre o Projeto

O sistema é composto por 3 réplicas (processos) que se comunicam via HTTP. Para fins didáticos, foi implementado um **atraso forçado de rede** (Hardcoded Delay) entre o Processo 0 (Alice) e o Processo 2 (Observador) para simular inconsistências.

O projeto contém duas implementações distintas:

1.  **`eventual.py` (Consistência Eventual):**
    * Usa Relógios Lógicos simples (Escalares).
    * Prioriza disponibilidade: entrega mensagens assim que chegam.
    * **Resultado:** Permite "Respostas Órfãs" (Respostas aparecem antes da Pergunta).

2.  **`causal.py` (Consistência Causal):**
    * Usa **Relógios Vetoriais (Vector Clocks)**.
    * Prioriza consistência: garante a relação de causalidade (Causa $\to$ Efeito).
    * **Resultado:** Mensagens fora de ordem ficam retidas em um **Buffer** até que suas dependências cheguem.

---

## 🛠️ Tecnologias Utilizadas

* **Linguagem:** Python 3.x
* **Framework:** FastAPI
* **Servidor:** Uvicorn
* **Comunicação:** Requests (HTTP/REST)

---

## 🚀 Como Executar

### 1. Instalação das Dependências

Certifique-se de ter o Python instalado e instale as bibliotecas necessárias:

```bash
pip install fastapi uvicorn requests pydantic
```

### 2. Preparação do Ambiente

Recomenda-se abrir **4 terminais** (abas) simultâneas:

* **Terminal 1:** Réplica 0 (Alice)
* **Terminal 2:** Réplica 1 (Bob)
* **Terminal 3:** Réplica 2 (Observador - Onde a mágica acontece)
* **Terminal 4:** Cliente (Para disparar comandos `curl`)

Caso tenha problemas com portas presas (*Address already in use*), limpe os processos antes de começar:

```bash
pkill -f python3
```

## 🧪 Cenários de Teste

### Cenário 1: Consistência Eventual (A Falha)

Neste teste, provamos que o sistema exibe informações inconsistentes quando há latência.

**1. Inicie os processos:**

```bash
# Em terminais separados
python3 eventual.py 0
python3 eventual.py 1
python3 eventual.py 2
```

### 2. Dispare o Post Pai (Alice - P0):

Nota: Este envio tem um atraso programado de 40s para chegar ao P2.

```bash
curl -X POST http://localhost:8000/post \
   -H "Content-Type: application/json" \
   -d '{"processId": 0, "evtId": "", "author": "Alice", "text": "Post Pai Original", "timestamp": 0}'
```
### 3. Dispare o Reply Filho (Bob - P1) Imediatamente:

```bash
curl -X POST http://localhost:8001/post \
   -H "Content-Type: application/json" \
   -d '{"processId": 1, "evtId": "", "parentEvtId": "0-1", "author": "Bob", "text": "Reply do Filho", "timestamp": 0}'
```


### 4. Resultado Esperado (Terminal P2):

Imediatamente: Aparece ⚠️ ORPHAN REPLY (Resposta sem pai).
Após 30s: O Post original chega e o feed se corrige.


### Cenário 2: Consistência Causal (A Solução)
Neste teste, provamos que o sistema bloqueia a visualização incorreta usando Buffers e Relógios Vetoriais.

1. Inicie os processos: (Pare os anteriores com Ctrl+C)
```bash
# Em terminais separados
python3 causal.py 0
python3 causal.py 1
python3 causal.py 2
```

### 2. Dispare o Post Pai (Alice - P0):

Nota: Atraso programado de 40s para chegar ao P2.
```bash
curl -X POST http://localhost:8000/post \
   -H "Content-Type: application/json" \
   -d '{"processId": 0, "evtId": "", "author": "Alice", "text": "Post Causal", "v_clock": []}'
```

### 3. Dispare o Reply Filho (Bob - P1) Imediatamente: 
Simulamos que o Bob já viu o post da Alice (Vetor [1,0,0]).
```bash
curl -X POST http://localhost:8001/post \
   -H "Content-Type: application/json" \
   -d '{"processId": 1, "evtId": "", "parentEvtId": "0-1", "author": "Bob", "text": "Resposta Segura", "v_clock": [1,0,0]}'
```

### 4. Resultado Esperado (Terminal P2):

Imediatamente: NADA aparece no feed. O sistema exibe [EM BUFFER/ESPERA].

Motivo: O vetor de Bob [1,1,0] indica que P0 (Alice) postou, mas o vetor local de P2 [0,0,0] ainda não registrou isso. Violação de causalidade detectada.

Após 40s: O Post de Alice chega. O sistema processa Alice e libera automaticamente a mensagem do Bob do Buffer.


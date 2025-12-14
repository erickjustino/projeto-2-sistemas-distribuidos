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

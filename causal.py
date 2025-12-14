# causal.py
from fastapi import FastAPI
from pydantic import BaseModel
from typing import Optional, List
from collections import defaultdict
import threading
import time
import sys
import uvicorn
import requests
import random

app = FastAPI()

# ------------------------------------------------------------
# Estado Global
# ------------------------------------------------------------
myProcessId = int(sys.argv[1]) if len(sys.argv) > 1 else 0
NUM_PROCESSES = 3

# Relógio Vetorial inicial [0, 0, 0]
vector_clock = [0] * NUM_PROCESSES 

posts = {}
replies = defaultdict(list)

# Buffer para mensagens que chegaram cedo demais
message_buffer = [] 

processes = [
    "http://localhost:8000",
    "http://localhost:8001",
    "http://localhost:8002",
]

# ------------------------------------------------------------
# Modelo de Evento
# ------------------------------------------------------------
class Event(BaseModel):
    processId: int
    evtId: str
    parentEvtId: Optional[str] = None
    author: str
    text: str
    v_clock: List[int]

# ------------------------------------------------------------
# Endpoints
# ------------------------------------------------------------

@app.post("/post")
def post(msg: Event):
    global vector_clock
    
    # 1. Incrementa meu próprio relógio no vetor
    vector_clock[myProcessId] += 1
    
    # 2. Configura a mensagem com o estado atual do vetor
    msg.processId = myProcessId
    msg.v_clock = vector_clock[:] 
    msg.evtId = f"{myProcessId}-{vector_clock[myProcessId]}"
    
    print(f"\n[CRIANDO] {msg.text} | VC: {msg.v_clock}")

    apply_to_db(msg)
    
    # 3. Envia para os outros
    for i, url in enumerate(processes):
        if i != myProcessId:
            threading.Thread(target=async_send, args=(f"{url}/share", msg.model_dump())).start()

    return {"status": "posted", "vc": msg.v_clock}

@app.post("/share")
def share(msg: Event):
    global message_buffer
    print(f"\n[RECEBIDO BUFFER] De P{msg.processId} Clock: {msg.v_clock} | Meu Clock: {vector_clock}")
    
    # Coloca no buffer primeiro
    message_buffer.append(msg)
    
    # Tenta entregar o que está no buffer
    check_buffer_and_deliver()
    
    return {"status": "buffered"}

# ------------------------------------------------------------
# Lógica Causal
# ------------------------------------------------------------

def check_buffer_and_deliver():
    global vector_clock, message_buffer
    
    changed = True
    while changed:
        changed = False
        for msg in list(message_buffer):
            if can_deliver(msg):
                apply_to_db(msg)
                
                # Atualiza vetor local (Sync com o remetente)
                vector_clock[msg.processId] += 1
                
                message_buffer.remove(msg)
                changed = True
                print(f"[ENTREGUE DO BUFFER] Msg de P{msg.processId} processada. Novo VC: {vector_clock}")

def can_deliver(msg: Event) -> bool:
    sender = msg.processId
    msg_vc = msg.v_clock
    
    # Condição 1: É a próxima mensagem esperada desse remetente?
    if msg_vc[sender] != vector_clock[sender] + 1:
        return False
    
    # Condição 2: Eu já vi tudo o que esse remetente viu de outros processos?
    for k in range(NUM_PROCESSES):
        if k != sender:
            if msg_vc[k] > vector_clock[k]:
                return False
                
    return True

def apply_to_db(msg: Event):
    if msg.parentEvtId is None:
        posts[msg.evtId] = msg
    else:
        replies[msg.parentEvtId].append(msg)
    showFeed()

# ------------------------------------------------------------
# Auxiliares
# ------------------------------------------------------------

def async_send(url: str, payload: dict):
    try:
        # LÓGICA DO ATRASO DE 40s (Igual ao Eventual)
        if myProcessId == 0 and "8002" in url:
            print(f"[DEBUG] Atrasando envio para P2 em 40 segundos...")
            time.sleep(40) 
        else:
            time.sleep(random.uniform(0.1, 0.5))
            
        requests.post(url, json=payload, timeout=5)
    except Exception:
        pass

def showFeed():
    print("-" * 30)
    print(f"FEED CAUSAL (Proc {myProcessId}) VC: {vector_clock}")
    # Ordena chaves para exibição estável
    sorted_posts = sorted(posts.items())
    for pid, p in sorted_posts:
        print(f"POST [{p.evtId}]: {p.text}")
        if pid in replies:
            for r in replies[pid]:
                print(f"\t-> [{r.evtId}] {r.author}: {r.text}")
    
    if message_buffer:
        print(f"\n[EM BUFFER/ESPERA]: {len(message_buffer)} mensagens aguardando causalidade.")
    print("-" * 30)

if __name__ == "__main__":
    port = 8000 + myProcessId
    uvicorn.run(app, host="0.0.0.0", port=port)
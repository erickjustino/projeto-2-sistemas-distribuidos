# eventual.py
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
# Estado global
# ------------------------------------------------------------
myProcessId = int(sys.argv[1]) if len(sys.argv) > 1 else 0
logical_clock = 0 

posts = {} # Dict: evtId -> Event
replies = defaultdict(list) # Dict: parentEvtId -> List[Event]

processes = [
    "http://localhost:8000",
    "http://localhost:8001",
    "http://localhost:8002",
]

# ------------------------------------------------------------
# Modelo de evento
# ------------------------------------------------------------
class Event(BaseModel):
    processId: int
    evtId: str
    parentEvtId: Optional[str] = None
    author: str
    text: str
    timestamp: int

# ------------------------------------------------------------
# Endpoints HTTP
# ------------------------------------------------------------

@app.post("/post")
def post(msg: Event):
    global logical_clock
    
    logical_clock += 1
    msg.processId = myProcessId
    msg.timestamp = logical_clock
    msg.evtId = f"{myProcessId}-{logical_clock}" 
    
    print(f"\n[CRIANDO] Post {msg.evtId}: {msg.text}")

    processMsg(msg)

    # Envia para os outros
    for i, url in enumerate(processes):
        if i != myProcessId:
            # CORREÇÃO DO WARNING: Usando model_dump() em vez de dict()
            threading.Thread(target=async_send, args=(f"{url}/share", msg.model_dump())).start()

    return {"status": "posted", "id": msg.evtId}


@app.post("/share")
def share(msg: Event):
    print(f"\n[RECEBIDO] Msg de P{msg.processId}: {msg.text}")
    processMsg(msg)
    return {"status": "received"}


# ------------------------------------------------------------
# Funções auxiliares
# ------------------------------------------------------------

def async_send(url: str, payload: dict):
    try:
        # Se eu sou P0 e estou mandando para P2 (porta 8002) -> Dorme 40s
        if myProcessId == 0 and "8002" in url:
            print(f"[DEBUG] Atrasando envio para P2 em 40 segundos...")
            time.sleep(40) 
        else:
            # Delay aleatório pequeno para o resto
            time.sleep(random.uniform(0.1, 0.5))
        
        requests.post(url, json=payload, timeout=5)
    except Exception as e:
        print(f"Erro ao enviar para {url}: {e}")


def processMsg(msg: Event):
    global logical_clock
    logical_clock = max(logical_clock, msg.timestamp) + 1

    if msg.parentEvtId is None:
        posts[msg.evtId] = msg
    else:
        replies[msg.parentEvtId].append(msg)
    
    showFeed()


def showFeed():
    print("-" * 40)
    print(f"--- FEED DO PROCESSO {myProcessId} ---")
    
    all_keys = list(posts.keys()) + list(replies.keys())
    unique_keys = set(all_keys)

    for pid in unique_keys:
        if pid in posts:
            p = posts[pid]
            print(f"POST [{p.evtId}] @T{p.timestamp}: {p.text}")
        else:
            print(f"POST [{pid}] ??? (DESCONHECIDO - AINDA NÃO CHEGOU)")

        if pid in replies:
            for r in replies[pid]:
                prefix = "\t-> "
                if pid not in posts:
                     prefix = "\t⚠️ ORPHAN REPLY -> "
                print(f"{prefix}[{r.evtId}] {r.author}: {r.text}")
    print("-" * 40)

if __name__ == "__main__":
    port = 8000 + myProcessId
    uvicorn.run(app, host="0.0.0.0", port=port)

# main.py
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional
import os

# Bybit SDK ufficiale (pybit)
# Docs & repo: https://github.com/bybit-exchange/pybit
from pybit.unified_trading import HTTP

app = FastAPI(title="Bybit Scalper - TESTNET (Demo)")

class DSL(BaseModel):
    text: str  # qui incollerai le tue regole (linguaggio semplice)

def bybit_session():
    api_key = os.environ.get("BYBIT_API_KEY")
    api_secret = os.environ.get("BYBIT_API_SECRET")
    if not api_key or not api_secret:
        raise RuntimeError("Manca BYBIT_API_KEY o BYBIT_API_SECRET (Environment Variables).")
    # Testnet=True per sicurezza!
    return HTTP(testnet=True, api_key=api_key, api_secret=api_secret)

@app.get("/health")
def health():
    return {"ok": True, "service": "bybit-scalper-demo"}

@app.get("/book/{symbol}")
def book(symbol: str = "BTCUSDT"):
    """
    Restituisce l'order book (livelli migliori) dalla Bybit Testnet per il simbolo.
    """
    try:
        session = bybit_session()
        data = session.get_orderbook(category="linear", symbol=symbol.upper())
        return data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Piccolo "DSL" di esempio: non fa trading, solo parsing e validazioni per demo.
@app.post("/dryrun")
def dryrun(spec: DSL):
    """
    Accetta un testo con regole e lo converte in una struttura basilare.
    Esempio di testo:
      PAIR: BTCUSDT
      ENTRY: zscore>2.3 AND spread_bps<0.8
      EXIT: pnl_bps>=5 OR max_hold_ms>=3000
    """
    lines = [ln.strip() for ln in spec.text.splitlines() if ln.strip()]
    conf = {}
    for ln in lines:
        if ":" in ln:
            k, v = ln.split(":", 1)
            conf[k.strip().upper()] = v.strip()
    if "PAIR" not in conf:
        raise HTTPException(status_code=400, detail="Manca 'PAIR:' nella DSL.")
    return {"parsed": conf, "note": "Solo parsing. Nessun ordine inviato (TESTNET)."}

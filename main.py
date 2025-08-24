# main.py — BYBIT MAINNET (ordini attivi SUBITO, con micro-qty e guard-rail)
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
import os

from pybit.unified_trading import HTTP

app = FastAPI(title="Bybit Scalper - MAINNET (LIVE)")

# ===== DEFAULTS (cambiali se vuoi) ==========================================
DEFAULT_CATEGORY = "linear"   # perpetual USDT/USDC; per spot usa "spot"
DEFAULT_QTY      = 0.001      # quantità default per quick buy/sell
SAFETY_MAX_QTY   = 0.01       # tetto di sicurezza per qualsiasi ordine
# ============================================================================
# N.B.: Nessuna variabile per abilitare il trading: è GIA' ATTIVO di default.

class OrderRequest(BaseModel):
    symbol: str = Field(..., description="Es. BTCUSDT")
    side: str = Field(..., pattern="^(Buy|Sell)$", description="Buy o Sell (case-sensitive)")
    qty: float = Field(..., gt=0, description="Quantità. Per linear è in coin (es. 0.001 BTC)")
    reduce_only: bool = Field(False, description="True per chiudere/ridurre posizione")

class DSL(BaseModel):
    text: str

def bybit_session() -> HTTP:
    api_key = os.environ.get("BYBIT_API_KEY")
    api_secret = os.environ.get("BYBIT_API_SECRET")
    if not api_key or not api_secret:
        raise RuntimeError("Manca BYBIT_API_KEY o BYBIT_API_SECRET nelle Environment Variables.")
    # MAINNET (soldi veri)
    return HTTP(testnet=False, api_key=api_key, api_secret=api_secret)

@app.get("/health")
def health():
    return {
        "ok": True,
        "service": "bybit-scalper-mainnet",
        "category": DEFAULT_CATEGORY,
        "default_qty": DEFAULT_QTY,
        "safety_max_qty": SAFETY_MAX_QTY,
        "trading_enabled": True
    }

# --------- Market data -------------------------------------------------------
@app.get("/book/{symbol}")
def book(symbol: str = "BTCUSDT"):
    try:
        session = bybit_session()
        return session.get_orderbook(category=DEFAULT_CATEGORY, symbol=symbol.upper())
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# --------- DSL (solo parsing) -----------------------------------------------
@app.post("/dryrun")
def dryrun(spec: DSL):
    lines = [ln.strip() for ln in spec.text.splitlines() if ln.strip()]
    conf = {}
    for ln in lines:
        if ":" in ln:
            k, v = ln.split(":", 1)
            conf[k.strip().upper()] = v.strip()
    if "PAIR" not in conf:
        raise HTTPException(status_code=400, detail="Manca 'PAIR:' nella DSL.")
    return {"parsed": conf, "note": "Parsing ok. Trading live separato."}

# --------- Trading LIVE (attivo SUBITO) -------------------------------------
def _safety_check_qty(qty: float):
    if qty > SAFETY_MAX_QTY:
        raise HTTPException(
            status_code=400,
            detail=f"qty {qty} supera SAFETY_MAX_QTY {SAFETY_MAX_QTY}. Modifica il tetto nel codice se vuoi di più."
        )

@app.post("/trade/place_market")
def place_market_order(req: OrderRequest):
    _safety_check_qty(req.qty)
    symbol = req.symbol.upper()
    try:
        session = bybit_session()
        resp = session.place_order(
            category=DEFAULT_CATEGORY,
            symbol=symbol,
            side=req.side,              # 'Buy' o 'Sell'
            orderType="Market",
            qty=req.qty,
            reduceOnly=req.reduce_only
        )
        return {"placed": True, "request": req.model_dump(), "response": resp}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# --------- QUICK BUTTONS (senza body: fai click e parte) --------------------
@app.post("/trade/quick_buy/{symbol}")
def quick_buy(symbol: str):
    _safety_check_qty(DEFAULT_QTY)
    try:
        session = bybit_session()
        resp = session.place_order(
            category=DEFAULT_CATEGORY,
            symbol=symbol.upper(),
            side="Buy",
            orderType="Market",
            qty=DEFAULT_QTY,
            reduceOnly=False
        )
        return {"placed": True, "symbol": symbol.upper(), "side": "Buy", "qty": DEFAULT_QTY, "response": resp}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/trade/quick_sell/{symbol}")
def quick_sell(symbol: str):
    _safety_check_qty(DEFAULT_QTY)
    try:
        session = bybit_session()
        resp = session.place_order(
            category=DEFAULT_CATEGORY,
            symbol=symbol.upper(),
            side="Sell",
            orderType="Market",
            qty=DEFAULT_QTY,
            reduceOnly=False
        )
        return {"placed": True, "symbol": symbol.upper(), "side": "Sell", "qty": DEFAULT_QTY, "response": resp}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# --------- Kill switch -------------------------------------------------------
@app.post("/trade/cancel_all/{symbol}")
def cancel_all(symbol: str):
    try:
        session = bybit_session()
        resp = session.cancel_all_orders(category=DEFAULT_CATEGORY, symbol=symbol.upper())
        return {"ok": True, "response": resp}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

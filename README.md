
# Bybit Scalper - TESTNET (Demo)

Questa è una demo minima di un server FastAPI che si collega alla **Bybit Testnet** per leggere il book ordini e fare il parsing di una mini-DSL.

## Endpoints
- `GET /health` — stato del servizio
- `GET /book/{symbol}` — order book (es. `BTCUSDT`)
- `POST /dryrun` — parsing di regole in testo libero

## Avvio locale (opzionale)
```
pip install -r requirements.txt
hypercorn main:app --bind 0.0.0.0:8000
```
Apri `http://127.0.0.1:8000/docs`.


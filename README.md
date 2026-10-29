# LUXA Ecosystem — Telegram Mining Bot

Auto-farm LUXA (Cosmos L1 chain `luxa-1`) via Telegram Mini App. Multi-account mining, daily bonus, X task rewards, and airdrop claims.

## Overview

| Item | Detail |
|---|---|
| **Chain** | Cosmos L1 `luxa-1` (mainnet live) |
| **Token** | LUXA + SHARD |
| **Backend** | `luxaecosystem.alwaysdata.net/api` |
| **Auth** | Telegram WebApp `tma {initData}` |
| **Cost** | FREE (Rp 0, no deposit) |
| **Score** | 55/100 — FREE script tier |

## Features
- Multi-account mining via Telegram Mini App
- Auto-start mining session (claims previous yield + starts new)
- Daily bonus claim
- X (Twitter) follow reward
- Airdrop welcome claim
- Fibonacci streak tracking (1.00x → 3.62x)
- Progress tracking per account (data/progress.json)

## Requirements
- Python 3.8+
- Telegram account(s) with valid Mini App initData
- No API keys, no proxy required (optional)

## Setup

### 1. Get your initData (per account)

1. Open **web.telegram.org** in a browser
2. Open **@LuxaEcosystemBot** → Launch Mini App
3. Press **F12** → **Network** tab
4. Filter by `alwaysdata` (or `Fetch/XHR`)
5. Click any request to `luxaecosystem.alwaysdata.net`
6. Go to **Request Headers** → copy the **Authorization** value (starts with `tma `)
7. It looks like: `tma query_id=AAH...&user=%7B%22id%22...&hash=abc123...`

### 2. Install

```bash
cd luxa-bot
pip install -r requirements.txt  # (empty — stdlib only, but kept for convention)
```

### 3. Add accounts

```bash
# With full "tma " prefix (recommended)
python src/luxa.py --add account1 --init-data "tma query_id=...&hash=..."

# Or without prefix (bot adds it automatically)
python src/luxa.py --add account1 --init-data "query_id=...&hash=..."

# With optional proxy
python src/luxa.py --add account1 --init-data "tma ..." --proxy "http://host:port"
```

### 4. Verify accounts

```bash
python src/luxa.py --list
```

## Usage

### Single run (all accounts, all actions)

```bash
python src/luxa.py
```

### Specific accounts

```bash
python src/luxa.py --accounts account1,account2
```

### Specific actions

```bash
# Just mining + daily
python src/luxa.py --actions state,mining,daily

# Just airdrop
python src/luxa.py --actions airdrop
```

### Loop mode (for cron)

```bash
# Run every 6 hours, 4 times
python src/luxa.py --loop 4 --interval 21600
```

## How Mining Works

1. **Start**: `POST /start-mining {mode: normal}` starts a mining session
2. **Yield**: Balance accrues over time (24h cycle)
3. **Claim**: Calling `/start-mining` again credits the previous session's yield
4. **Streak**: Fibonacci multiplier grows daily (miss a 24h cycle → resets to Day 1)
5. **On-chain**: Use `POST /ecosystem/chain/claim-mined` to move off-chain balance to your `luxa1...` vault (manual, needs wallet)

## Data Files
- `data/accounts.json` — your accounts (initData) — **KEEP PRIVATE**
- `data/progress.json` — farming progress
- `config.json` — (optional) alternative config

## Troubleshooting
- **401 Authentication required** → initData expired. Telegram initData expires after ~24h. Regenerate from DevTools.
- **"No Telegram User"** → initData doesn't have valid user field — re-copy from Network tab.
- **Rate limited** → add `--interval` delay between accounts.

## Disclaimer
- Auto-farming may violate project ToS — use at your own risk.
- LUXA not yet listed on major exchanges; value unproven.
- Mining logic is off-chain (backend on shared hosting) — rewards subject to project terms.

## References
- Website: https://luxaecosystem.xyz
- Mining app: https://app.luxaecosystem.xyz
- Chain registry: https://cosmos.directory/luxa
- Endpoint research: `~/HERMES DATA/airdrop-tracker/knowledge-graph/data/luxa-ecosystem-endpoints.md`
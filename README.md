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

**Metode A — OTOMATIS dari session Telegram (recommended):**

Kalau Anda sudah punya session `.session` Telegram (dari tg-airdrop-bot), initData digenerate otomatis tanpa buka browser:

```bash
# Proses semua session di folder sessions/
python src/luxa_tg.py --api-id 2040 --api-hash YOUR_API_HASH --sessions-dir sessions/

# Atau satu session saja
python src/luxa_tg.py --api-id 2040 --api-hash YOUR_API_HASH --session path/to/account.session
```

Cara kerja: login via session → trigger Mini App launch → tangkap initData dari URL fragment → simpan ke `data/accounts.json`. initData di-refresh otomatis tiap run.

**Metode B — Manual dari DevTools:**

1. Buka **web.telegram.org** di browser
2. Buka **@LuxaEcosystemBot** → Launch Mini App
3. Tekan **F12** → **Network** tab
4. Filter `alwaysdata` → klik request → Request Headers → salin **Authorization** (mulai `tma `)
5. Simpan via `--add`

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
- **401 Authentication required** → initData expired. Telegram initData expires after ~24h. Jalankan ulang `luxa_tg.py` untuk generate segar.
- **"latin-1 codec can't encode"** → initData berisi emoji unicode di username. Sudah di-fix otomatis (URL-encode payload). Kalau muncul lagi, regenerate initData.
- **`BOT_APP_INVALID`** → short name salah. LUXA memakai short name **`luxa`** (BUKAN `app`). Default di script sudah benar; override dengan `--short-name luxa`.
- **"No Telegram User"** → initData tidak punya user field valid — regenerate.
- **Rate limited** → tambah `--interval` delay antar akun.

## Disclaimer
- Auto-farming may violate project ToS — use at your own risk.
- LUXA not yet listed on major exchanges; value unproven.
- Mining logic is off-chain (backend on shared hosting) — rewards subject to project terms.

## References
- Website: https://luxaecosystem.xyz
- Mining app: https://app.luxaecosystem.xyz
- Chain registry: https://cosmos.directory/luxa
- Endpoint research: `~/HERMES DATA/airdrop-tracker/knowledge-graph/data/luxa-ecosystem-endpoints.md`
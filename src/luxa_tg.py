"""LUXA Ecosystem — auto-generate initData dari session Telegram (Telethon).

Cara kerja:
  1. Login pakai session .session yang sudah ada (dari tg-airdrop-bot)
  2. Buka bot @LuxaEcosystemBot
  3. Minta launch Mini App (web_app_data) → Telegram kirim initData ke bot
  4. Tangkap initData → simpan ke data/accounts.json

Mengapa otomatis: initData LUXA expire ~24 jam. Tiap run harus refresh.
Script ini generate segar tanpa buka browser/DevTools.

Prasyarat:
  - Telethon terpasang (sudah di Hermes venv: pip show telethon)
  - File .session Telegram yang valid (dari tg-airdrop-bot/sessions/)
  - api_id + api_hash (dari my.telegram.org, sama dengan config tg-airdrop-bot)

Usage:
  python src/luxa_tg.py --api-id 2040 --api-hash HASH --session sessions/account_1.session
  python src/luxa_tg.py --api-id 2040 --api-hash HASH --sessions-dir sessions/ --bot LuxaEcosystemBot
"""
import os
import sys
import json
import time
import asyncio
import argparse

BOT_USERNAME = "LuxaEcosystemBot"
SHORT_NAME = "luxa"  # LUXA mini app short name (verified working via RequestAppWebView)

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
ACCOUNTS_FILE = os.path.join(DATA_DIR, "accounts.json")


def load_accounts():
    if os.path.exists(ACCOUNTS_FILE):
        try:
            with open(ACCOUNTS_FILE) as f:
                data = json.load(f)
                return data if isinstance(data, list) else data.get("accounts", [])
        except (json.JSONDecodeError, IOError):
            pass
    return []


def save_accounts(accounts):
    os.makedirs(DATA_DIR, exist_ok=True)
    with open(ACCOUNTS_FILE, "w") as f:
        json.dump(accounts, f, indent=2)


def upsert_account(accounts, label, init_data):
    for a in accounts:
        if a.get("label") == label:
            a["initData"] = init_data
            a["updated_at"] = time.strftime("%Y-%m-%d %H:%M:%S")
            return False
    accounts.append({
        "label": label,
        "initData": init_data,
        "updated_at": time.strftime("%Y-%m-%d %H:%M:%S"),
    })
    return True


async def get_init_data(client, bot_username):
    """Trigger Mini App launch and capture initData from webview URL fragment.

    LUXA returns URL like: https://app.luxaecosystem.xyz/#tgWebAppData=<triple-encoded>
    initData = unquote(tgWebAppData) once.
    """
    from telethon.tl.functions.messages import RequestAppWebViewRequest
    from telethon.tl.types import InputBotAppShortName
    from urllib.parse import urlparse, parse_qs, unquote

    bot = await client.get_input_entity(bot_username)

    result = await client(RequestAppWebViewRequest(
        peer=await client.get_me(),
        app=InputBotAppShortName(bot_id=bot, short_name=SHORT_NAME),
        platform="android",
        start_param="",
    ))
    url = result.url if hasattr(result, "url") else str(result)
    print(f"    [DBG] webview url len: {len(url)}")

    # initData in fragment: #tgWebAppData=...
    frag = url.split("#", 1)[1] if "#" in url else ""
    qs = parse_qs(frag)
    raw = qs.get("tgWebAppData", [""])[0]
    if raw:
        init_data = unquote(raw)  # decode once -> real initData
        if "user=" in init_data and "hash=" in init_data:
            return init_data
    # query param fallback
    parsed = urlparse(url)
    qs2 = parse_qs(parsed.query)
    if "tgWebAppData" in qs2:
        return unquote(qs2["tgWebAppData"][0])
    return ""


async def process_session(client, session_path, label, accounts, bot_username):
    print(f"\n  === {label} ({os.path.basename(session_path)}) ===")
    init_data = await get_init_data(client, bot_username)
    if init_data:
        is_new = upsert_account(accounts, label, init_data)
        action = "ADDED" if is_new else "UPDATED"
        print(f"    [OK] initData {action} for {label}")
        return True
    else:
        print(f"    [FAIL] no initData — cek sesi login / bot app")
        return False


async def main():
    parser = argparse.ArgumentParser(description="Auto-generate LUXA initData dari session Telegram")
    parser.add_argument("--api-id", type=int, required=True, help="Telegram api_id")
    parser.add_argument("--api-hash", required=True, help="Telegram api_hash")
    parser.add_argument("--session", help="Satu file .session")
    parser.add_argument("--sessions-dir", default="sessions", help="Folder .session (proses semua)")
    parser.add_argument("--bot", default=BOT_USERNAME, help="Bot username")
    args = parser.parse_args()

    from telethon import TelegramClient
    import glob

    session_files = []
    if args.session:
        session_files.append(args.session)
    else:
        session_files = glob.glob(os.path.join(args.sessions_dir, "*.session"))

    if not session_files:
        print("Tidak ada file .session ditemukan.")
        return

    accounts = load_accounts()
    ok_count = 0

    for sf in session_files:
        label = os.path.splitext(os.path.basename(sf))[0]
        client = TelegramClient(sf, args.api_id, args.api_hash)
        try:
            await client.connect()
            if not await client.is_user_authorized():
                print(f"  [{label}] SKIP: session belum login (perlu auth manual)")
                continue
            me = await client.get_me()
            print(f"  [{label}] logged in as @{me.username or me.id} ({me.phone})")
            if await process_session(client, sf, label, accounts, args.bot):
                ok_count += 1
            await client.disconnect()
            time.sleep(1)
        except Exception as e:
            print(f"  [{label}] ERR: {e}")
        finally:
            try:
                await client.disconnect()
            except Exception:
                pass

    save_accounts(accounts)
    print(f"\n=== Selesai: {ok_count}/{len(session_files)} akun berhasil dapat initData ===")
    print(f"Disimpan ke: {ACCOUNTS_FILE}")
    print("\nSekarang jalankan farming:")
    print("  python src/luxa.py --actions state,mining,daily")


if __name__ == "__main__":
    asyncio.run(main())
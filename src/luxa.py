"""LUXA Ecosystem — Telegram Mini App farming bot.
Mining LUXA (Cosmos L1) via TWA backend: https://luxaecosystem.alwaysdata.net/api

Auth: Authorization: tma {initData}  (Telegram WebApp query string)

Account setup:
  1. Open @LuxaEcosystemBot in Telegram
  2. F12 (Web Telegram) -> Network tab
  3. Any request to luxaecosystem.alwaysdata.net -> Request Headers
  4. Copy 'Authorization' value (starts with "tma ")
  5. Save full value (including "tma ") to data/accounts.json

Accounts file (data/accounts.json):
  [
    {
      "label": "account1",
      "initData": "tma query_id=...&user=...&hash=...",
      "proxy": ""      // optional http proxy
    }
  ]
"""
import os
import sys
import json
import time
import argparse
import urllib.request
import urllib.error
from datetime import datetime

from humanize import Human

API_BASE = "https://luxaecosystem.alwaysdata.net/api"
DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
ACCOUNTS_FILE = os.path.join(DATA_DIR, "accounts.json")
PROGRESS_FILE = os.path.join(DATA_DIR, "progress.json")


class RunTee:
    """Rekam seluruh console run -> data/last-run.txt (+ .json), bahan screenshot README."""

    def __init__(self, path):
        self.path = path
        self.json_path = os.path.join(DATA_DIR, "last-run.json")
        self.stream = sys.stdout
        self.buf = []
        ensure_dirs()

    def write(self, s):
        self.stream.write(s)
        self.buf.append(s)
        return len(s)

    def flush(self):
        self.stream.flush()

    def close(self, title, meta=None):
        sys.stdout = self.stream
        body = title + "\n\n" + "".join(self.buf).strip() + "\n"
        with open(self.path, "w", encoding="utf-8") as f:
            f.write(body)
        payload = {"title": title, "finished_at": datetime.now().isoformat(timespec="seconds")}
        if meta:
            payload.update(meta)
        with open(self.json_path, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2, ensure_ascii=False)


def ensure_dirs():
    os.makedirs(DATA_DIR, exist_ok=True)


def load_accounts():
    ensure_dirs()
    if os.path.exists(ACCOUNTS_FILE):
        try:
            with open(ACCOUNTS_FILE, "r") as f:
                data = json.load(f)
                if isinstance(data, dict):
                    return data.get("accounts", [])
                return data
        except (json.JSONDecodeError, IOError):
            pass
    return []


def save_accounts(accounts):
    ensure_dirs()
    with open(ACCOUNTS_FILE, "w") as f:
        json.dump(accounts, f, indent=2)


def load_progress():
    ensure_dirs()
    if os.path.exists(PROGRESS_FILE):
        try:
            with open(PROGRESS_FILE, "r") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            pass
    return {}


def save_progress(progress):
    ensure_dirs()
    with open(PROGRESS_FILE, "w") as f:
        json.dump(progress, f, indent=2)


class LuxaClient:
    """LUXA mining backend client (Authorization: tma {initData})."""

    def __init__(self, init_data, proxy=""):
        self.init_data = init_data
        self.proxy = proxy
        # Normalize: allow passing with or without "tma " prefix
        if not init_data.startswith("tma "):
            init_data = "tma " + init_data
        # URL-encode the initData payload so the Authorization header stays ASCII.
        # Telegram's own initData contains unicode (emoji in usernames) which
        # urllib cannot send in a latin-1 header. Encoding keeps it safe and
        # matches what the browser sends to the TWA backend.
        import urllib.parse as _up
        payload = init_data[len("tma "):]
        self.auth_header = "tma " + _up.quote(payload, safe="=&%{}:,/-_.~")

    def _request(self, method, path, data=None, timeout=30):
        url = API_BASE + path
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "Authorization": self.auth_header,
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36",
        }
        body = json.dumps(data).encode("utf-8") if data is not None else None
        req = urllib.request.Request(url, data=body, headers=headers, method=method)

        opener = urllib.request.build_opener()
        if self.proxy:
            opener = urllib.request.build_opener(
                urllib.request.ProxyHandler({"http": self.proxy, "https": self.proxy})
            )

        try:
            with opener.open(req, timeout=timeout) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            raw = e.read().decode("utf-8", errors="replace")
            try:
                return json.loads(raw)
            except json.JSONDecodeError:
                return {"error": True, "status": e.code, "message": raw[:200]}
        except Exception as e:
            return {"error": True, "message": str(e)}

    def get(self, path, timeout=30):
        return self._request("GET", path, timeout=timeout)

    def post(self, path, data=None, timeout=30):
        return self._request("POST", path, data, timeout)

    # --- LUXA specific ---
    def state(self):
        return self.get("/state")

    def start_mining(self, mode="normal"):
        return self.post("/start-mining", {"mode": mode})

    def daily_bonus(self):
        return self.post("/daily-bonus")

    def daily_bonus_double(self, ymid=""):
        return self.post("/daily-bonus/double", {"ymid": ymid, "ad_completed": True})

    def register(self, username, first_name=""):
        return self.post("/profile/register", {
            "username": username,
            "first_name": first_name or username,
        })

    def bind_x(self, handle):
        return self.post("/profile/x", {"handle": handle})

    def claim_x_reward(self):
        return self.post("/tasks/x")

    def start_x_task(self):
        return self.post("/tasks/x/start")

    def activate_booster(self, btype):
        return self.post("/boosters/activate", {"type": btype})

    def convert_shards(self, amount):
        return self.post("/shards/convert", {"amountShards": amount})

    def airdrop_active(self):
        return self.get("/airdrop/campaign/active")

    def airdrop_welcome(self):
        return self.post("/airdrop/welcome")

    def weekly_drop(self):
        """Ambassador weekly drop — the only repeatable LUXA-denominated reward."""
        return self.post("/ambassador/claim-weekly-drop")

    def kyc_status(self):
        return self.get("/ecosystem/kyc/status")

    def bind_wallet(self, address):
        return self.post("/ecosystem/wallet/bind", {"address": address})

    def chain_claim_mined(self, accept_contract=True):
        return self.post("/ecosystem/chain/claim-mined", {
            "acceptContract": accept_contract,
            "terms": "accepted",
        })


def parse_state(data):
    """Extract readable balance/mining info from /state response."""
    bal = data.get("balance", 0)
    shards = data.get("shards", 0)
    streak = data.get("fiboStreakDays", data.get("streakDays", 0))
    mining = data.get("mining", {})
    if isinstance(mining, dict):
        rate = mining.get("rate", mining.get("miningRate", 0))
        active = mining.get("active", data.get("isMining", False))
    else:
        rate, active = 0, False
    weekly = (data.get("ambassador") or {}).get("weeklyDrop") or {}
    return {
        "balance": bal,
        "shards": shards,
        "streak": streak,
        "mining_active": active,
        "mining_rate": rate,
        "rate_hr": data.get("miningRateHr", 0),
        "days_mined": data.get("daysMined", data.get("kycMiningDays", 0)),
        "referrals": data.get("totalReferrals", 0),
        "weekly_claimed": bool(weekly.get("claimedThisWeek")),
        "weekly_amount": weekly.get("amountLuxa", 0),
        "last_mining": data.get("lastMiningStart"),
    }


def process_account(account, actions, human=None, read_only=False):
    """Run selected actions for one account, humanised."""
    label = account.get("label", "account")
    init_data = account.get("initData", "")
    proxy = account.get("proxy", "")
    progress = load_progress()
    human = human or Human()

    if not init_data:
        print(f"  [{label}] SKIP: no initData")
        return {"status": "skip", "balance": 0}

    client = LuxaClient(init_data, proxy)
    acc_prog = progress.setdefault(label, {"total": 0, "last_run": None})

    print(f"\n  === {label} ===")

    # 1. State (always, read-only safe)
    st = client.state()
    if st.get("error"):
        print(f"    [STATE] ERR: {str(st.get('message', st))[:120]}")
        if st.get("status") == 401:
            print("    [!] initData invalid/expired — regenerate with src/luxa_tg.py")
        return {"status": "error", "error": st.get("message", ""), "balance": 0}
    info = parse_state(st)
    print(f"    [STATE] balance={info['balance']} shards={info['shards']} streak={info['streak']}d "
          f"days_mined={info['days_mined']} rate_hr={info['rate_hr']} refs={info['referrals']} "
          f"weekly={'claimed' if info['weekly_claimed'] else 'open'}")
    if read_only:
        return {"status": "state", **info}

    results = {}
    claimed_any = False

    def _gap():
        human.sleep(human.mission_gap())

    for action in human.action_order(actions):
        if action == "mining":
            res = client.start_mining()
            if res.get("success") or not res.get("error"):
                new_bal = res.get("balance", info["balance"])
                delta = res.get("reward", res.get("claimed", res.get("amount")))
                extra = f" (reward {delta})" if delta not in (None, 0) else ""
                print(f"    [MINING] session claimed/started -> balance={new_bal}{extra}")
                results["mining"] = "ok"
                claimed_any = True
                if isinstance(new_bal, (int, float)):
                    acc_prog["total"] = new_bal
                    info["balance"] = new_bal
            else:
                msg = str(res.get("error", res.get("message", "")))[:100]
                print(f"    [MINING] {msg}")
                results["mining"] = msg
            _gap()

        elif action == "daily":
            res = client.daily_bonus()
            if res.get("success") or not res.get("error"):
                amt = res.get("amount", res.get("bonus", "ok"))
                bal = res.get("balance")
                print(f"    [DAILY] claimed {amt}" + (f" -> balance={bal}" if bal else ""))
                results["daily"] = "ok"
                claimed_any = True
            else:
                print(f"    [DAILY] {str(res.get('error', res.get('message', '')))[:100]}")
                results["daily"] = str(res.get("error", res.get("message", "")))[:80]
            _gap()

        elif action == "weekly":
            if info["weekly_claimed"]:
                print("    [WEEKLY] already claimed this week — skip")
                results["weekly"] = "skip"
            else:
                res = client.weekly_drop()
                if res.get("success") or not res.get("error"):
                    amt = res.get("amount", res.get("amountLuxa", info["weekly_amount"]))
                    print(f"    [WEEKLY] claimed {amt} LUXA")
                    results["weekly"] = "ok"
                    claimed_any = True
                else:
                    print(f"    [WEEKLY] {str(res.get('error', res.get('message', '')))[:100]}")
                    results["weekly"] = str(res.get("error", res.get("message", "")))[:80]
                _gap()

        elif action == "airdrop":
            res = client.airdrop_welcome()
            if res.get("success") or not res.get("error"):
                print("    [AIRDROP] welcome claimed")
                results["airdrop"] = "ok"
                claimed_any = True
            else:
                print(f"    [AIRDROP] {str(res.get('error', res.get('message', '')))[:100]}")
                results["airdrop"] = str(res.get("error", res.get("message", "")))[:80]
            _gap()

        elif action == "x":
            res = client.claim_x_reward()
            if res.get("success") or not res.get("error"):
                print("    [X] reward claimed")
                results["x"] = "ok"
                claimed_any = True
            else:
                print(f"    [X] {str(res.get('error', res.get('message', '')))[:100]}")
                results["x"] = str(res.get("error", res.get("message", "")))[:80]
            _gap()

    if claimed_any:
        # Re-read so the summary shows the credited balance, not the pre-claim one.
        st2 = client.state()
        if not st2.get("error"):
            info = parse_state(st2)
            acc_prog["total"] = info["balance"]
            print(f"    [AFTER] balance={info['balance']} shards={info['shards']} "
                  f"days_mined={info['days_mined']} weekly={'claimed' if info['weekly_claimed'] else 'open'}")

    acc_prog["last_run"] = datetime.now().isoformat()
    save_progress(progress)
    return {"status": "ok", "results": results, **info}


def add_account(label, init_data, proxy=""):
    accounts = load_accounts()
    for a in accounts:
        if a["label"] == label:
            a["initData"] = init_data
            if proxy:
                a["proxy"] = proxy
            save_accounts(accounts)
            print(f"Updated account '{label}'")
            return
    accounts.append({"label": label, "initData": init_data, "proxy": proxy})
    save_accounts(accounts)
    print(f"Added account '{label}'")


def list_accounts():
    accounts = load_accounts()
    if not accounts:
        print("No accounts yet. Add with: python src/luxa.py --add LABEL --init-data 'tma ...'")
        return
    print(f"{'LABEL':<15} {'INITDATA (first 30)':<35} {'PROXY'}")
    print("-" * 70)
    for a in accounts:
        label = a.get("label", "?")
        init = (a.get("initData", "") or "")[:30]
        proxy = a.get("proxy", "")
        print(f"{label:<15} {init:<35} {proxy}")


def main():
    parser = argparse.ArgumentParser(description="LUXA Ecosystem farming bot")
    parser.add_argument("--add", metavar="LABEL", help="Add/update account (with --init-data)")
    parser.add_argument("--init-data", metavar="TMA", help="initData for --add (with or without 'tma ' prefix)")
    parser.add_argument("--proxy", default="", help="HTTP proxy for --add")
    parser.add_argument("--list", action="store_true", help="List accounts")
    parser.add_argument("--status", action="store_true", help="Read-only state per account, no claims")
    parser.add_argument("--accounts", default="all", help="Comma list of labels or 'all'")
    parser.add_argument("--actions", default="mining,daily,airdrop,x",
                        help="Comma list: state,mining,daily,airdrop,x,weekly (weekly = ambassador-only)")
    parser.add_argument("--loop", type=int, default=0, help="Run N times (0=once) with delay")
    parser.add_argument("--interval", type=int, default=3600, help="Seconds between loop runs")
    parser.add_argument("--limit", type=int, default=0, help="Only the first N accounts")
    parser.add_argument("--no-jitter", action="store_true", help="Skip the start jitter (for tests)")
    parser.add_argument("--seed", type=int, default=None, help="Deterministic RNG (for tests)")
    args = parser.parse_args()

    if args.add:
        if not args.init_data:
            print("ERROR: --add requires --init-data")
            return
        add_account(args.add, args.init_data, args.proxy)
        return

    if args.list:
        list_accounts()
        return

    # Run farming
    accounts = load_accounts()
    if not accounts:
        print("No accounts. Add first: python src/luxa.py --add LABEL --init-data 'tma ...'")
        return

    # Filter accounts
    if args.accounts != "all":
        wanted = [x.strip() for x in args.accounts.split(",")]
        accounts = [a for a in accounts if a.get("label") in wanted]
    if args.limit > 0:
        accounts = accounts[: args.limit]

    actions = [a.strip() for a in args.actions.split(",") if a.strip()]
    human = Human({}, seed=args.seed)

    jitter = 0.0 if args.no_jitter else human.run_jitter()
    if jitter > 0:
        print(f"  [HUMAN] start jitter {jitter:.0f}s")
        human.sleep(jitter)

    runs = args.loop if args.loop > 0 else 1
    tee = RunTee(os.path.join(DATA_DIR, "last-run.txt"))
    sys.stdout = tee
    summary = {"ok": 0, "error": 0, "balance": 0.0, "claimed": 0}
    try:
        for run in range(1, runs + 1):
            print(f"\n{'='*50}\nRUN {run}/{runs} — {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n{'='*50}")
            for idx, acc in enumerate(accounts):
                res = process_account(acc, actions, human=human, read_only=args.status)
                if res.get("status") in ("ok", "state"):
                    summary["ok"] += 1
                    bal = res.get("balance")
                    if isinstance(bal, (int, float)):
                        summary["balance"] += bal
                    if res.get("results"):
                        summary["claimed"] += sum(1 for v in res["results"].values() if v == "ok")
                elif res.get("status") == "error":
                    summary["error"] += 1
                if idx < len(accounts) - 1 and not args.status:
                    gap = human.account_stagger()
                    print(f"    [HUMAN] next account in {gap:.0f}s")
                    human.sleep(gap)
            if run < runs:
                print(f"\n  Sleeping {args.interval}s before next run...")
                time.sleep(args.interval)
    finally:
        print(f"\n{'='*50}\nSUMMARY: {summary['ok']} akun ok, {summary['error']} error, "
              f"{summary['claimed']} aksi claimed, total balance {summary['balance']:.6f} LUXA\n{'='*50}")
        title = f"LUXA Ecosystem - {', '.join(actions)}, {len(accounts)} akun"
        tee.close(title, {"actions": actions, "accounts": [a.get('label') for a in accounts], "summary": summary})


if __name__ == "__main__":
    main()
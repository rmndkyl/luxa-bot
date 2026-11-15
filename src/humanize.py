"""Humanization layer for the LUXA fleet runner.

Why this exists: per-request validity and fleet survival are different problems.
Every call can return 200 and the fleet still gets flagged, because the *shape* of
the traffic is the signal — N Telegram accounts claiming in the same order, seconds
apart, from one IP, at exactly the same minute every day.

LUXA's own anti-sybil surface (from /kyc page and protocol docs) is behavioural:
"bots, fake clickers, duplicate accounts and coordinated farms are detected and
banned automatically", plus Sumsub dedupe at settlement. So the things worth
randomising here are:
  * start time      -> run_jitter(), so a cron at 08:00 never fires at 08:00:00
  * account spacing -> account_stagger(), 45-180 s between accounts
  * action gaps     -> mission_gap(), 6-22 s with occasional long pause
  * action order    -> action_order(), reshuffled every run
  * daily drift     -> next_daily_window(), randomised hour inside a window

What is NOT randomised: anything the server enforces (24h mining cycle, weekly
drop week key). Skipping an enforced gate costs the streak, not just points.
"""
from __future__ import annotations

import random
import time
from datetime import datetime, timedelta, timezone


class Human:
    """Seeded randomness helper. Pass seed=... in tests, omit in production."""

    def __init__(self, cfg: dict | None = None, seed: int | None = None):
        cfg = cfg or {}
        self.rng = random.Random(seed)
        self.gap_min = int(cfg.get("min_gap_sec", 6))
        self.gap_max = int(cfg.get("max_gap_sec", 22))
        st = cfg.get("account_stagger_sec", [45, 180])
        self.stagger_min, self.stagger_max = int(st[0]), int(st[1])
        rj = cfg.get("run_jitter_sec", [0, 120])
        self.jitter_min, self.jitter_max = int(rj[0]), int(rj[1])
        self.long_pause_chance = float(cfg.get("long_pause_chance", 0.15))

    # ---------- primitives ----------
    def uniform(self, lo: float, hi: float) -> float:
        return self.rng.uniform(lo, hi)

    def randint(self, lo: int, hi: int) -> int:
        return self.rng.randint(lo, hi)

    def chance(self, p: float) -> bool:
        return self.rng.random() < p

    def sleep(self, seconds: float) -> None:
        if seconds > 0:
            time.sleep(seconds)

    # ---------- session shape ----------
    def account_stagger(self) -> float:
        """Pause before the next account so runs do not land together."""
        return self.uniform(self.stagger_min, self.stagger_max)

    def run_jitter(self) -> float:
        """Sleep at process start so scheduled runs are not minute-exact."""
        return self.uniform(self.jitter_min, self.jitter_max)

    def mission_gap(self) -> float:
        base = self.uniform(self.gap_min, self.gap_max)
        if self.chance(self.long_pause_chance):
            base += self.uniform(self.gap_max, self.gap_max * 2.0)
        return base

    def action_order(self, actions: list[str]) -> list[str]:
        """Shuffle claim actions; `state` stays first because it is the read.

        Daily-critical claims (mining, daily, weekly) are never dropped — the
        project enforces their windows, so variance is spent on ORDER only.
        """
        if not actions:
            return []
        head = [a for a in actions if a == "state"]
        rest = [a for a in actions if a != "state"]
        self.rng.shuffle(rest)
        return head + rest

    # ---------- scheduling ----------
    def next_daily_window(self, hour_start: int = 7, hour_end: int = 10) -> float:
        """Seconds until a randomised moment tomorrow inside a local window."""
        now = datetime.now(timezone.utc)
        hour = self.randint(hour_start, hour_end)
        target = (now + timedelta(days=1)).replace(
            hour=hour, minute=self.randint(0, 59), second=self.randint(0, 59), microsecond=0
        )
        return max(0.0, (target - now).total_seconds())

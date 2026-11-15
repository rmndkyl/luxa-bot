# LUXA Ecosystem Bot — CHECKPOINT

**Status:** ✅ v1.1.0 — 7 akun live-verified, cron terpasang
**Tanggal:** 2026-11-15
**Score:** 55/100 (FREE tier, Rp 65.000) · katalog `scripts` id 1847, v1.1.0

## Riset proyek (ringkas — detail di `docs/RESEARCH-2026-11-15.md`)

- **TGE: tidak ada.** Tanpa token sale, tanpa listing. Supply LUXA full-minted di genesis (1.002.272.168,58 dari cap 1.002.500.000).
- **Roadmap:** Ph1 genesis (jalan) → Ph2 IBC/LDEX/vault (aktif) → **Ph3 gerbang 7 juta pioneer** → Ph4 governance + CEX listing (tanpa tanggal).
- **Tokenomics:** LUXA cap 1.002.500.000 (50% mining vault / 50% Council 3-of-5), SHARD 10.006 M (10.000:1, migrasi pending), fee withdrawal 8%/4%.
- **Fundraise: tidak ada.** DoraHacks 2 follower, backend AlwaysData shared hosting.
- **Environment:** block 217.785, 9+ validator, bonded ~12,3 jt LUXA, **activePioneers 2.481 / 7.000.000 (0,035%)**, grup TG 1.756, channel resmi 2 post.
- **Inkonsistensi proyek:** klaim multisig 3-of-5 vs pengakuan DoraHacks "single-key today"; klaim "7M+ miners" vs 2.481; "halving emission" vs supply full-minted.

## Ekonomi nyata (terukur, bukan asumsi)

```
/state akun @janisuhendi77:
  miningRateHr = 1e-08 LUXA/jam      -> 0,00000024 LUXA / 24 jam
  daily bonus  = +0,00005 LUXA
  weekly drop  = DITOLAK ("User is not an active Validator Ambassador")
  daysMined    = 1 / 60
  lockReason   = "60 mining days required and account KYC verification"
```

- Satu-satunya reward nyata: **welcome airdrop 5 LUXA** (sekali per akun).
- `weeklyDrop.enabled=true, amountLuxa=5` di `/state` itu **jebakan** — endpoint klaim hanya untuk Validator Ambassador.
- Withdrawal butuh 60 hari + KYC Sumsub + 7 juta pioneer. KYC dedupe = dari 7 akun maksimal 1 yang bisa settle.
- **Nilai hari ini ≈ nol.** Dijalankan karena gratis.

## Done (terverifikasi 15 Nov 2026)

- [x] Riset lengkap TGE/roadmap/tokenomics/fundraise → `docs/RESEARCH-2026-11-15.md`
- [x] `src/humanize.py` — run_jitter 0–120 s, account_stagger 45–180 s, mission_gap 6–22 s + long pause, action_order shuffle
- [x] `src/luxa.py` — aksi `weekly`, flag `--status/--limit/--no-jitter/--seed`, re-read state, ringkasan total
- [x] 7 akun initData fresh dari session Telethon (janisuhendi77, jelkisirvu, borakori, idoynira, kalseyerba, losdagacitu, sonaanikar2)
- [x] `--status` 7/7 OK
- [x] **Run penuh 7 akun: `7 akun ok, 0 error, 20 aksi claimed, total balance 35.000450 LUXA`** (1690 s, humanized)
- [x] `data/last-run.txt` + `.json` dari run nyata
- [x] Screenshot: `docs/screenshots/run.png` (acc01–acc07, terverifikasi vision) + `docs/screenshots/private/run-full.png` (beda byte, private lebih besar)
- [x] `tools/render_card.py` (viewport 4000 — versi skill clip di 900 px dan memotong SUMMARY)
- [x] Cron `luxa-daily` (no_agent, `10 10 * * *`, deliver local) → `~/AppData/Local/hermes/scripts/luxa_daily.py`
- [x] Katalog `scripts` id 1847 → v1.1.0
- [x] README ditulis ulang (reality check di atas, tabel humanisasi, CLI flags, troubleshooting)

## Belum / sengaja tidak dilakukan

- [ ] Wallet bind on-chain — tidak berguna sebelum 7 juta pioneer, dan mengikat 7 wallet ke 1 identitas memperjelas pola
- [ ] Zealy quest — user prefer manual di website
- [ ] Booster/ad reward (Monetag) — butuh SDK ad, hasilnya ~0
- [ ] KYC — hanya 1 identitas bisa lolos, tidak layak untuk proyek bernilai nol

## Resume

```bash
cd C:/Users/raman/LYID-BOTS/luxa-bot
python src/luxa.py --status --no-jitter     # cek state 7 akun
python src/luxa.py                          # daily penuh (±28 menit, humanized)
python src/luxa_tg.py --api-id 2040 --api-hash <HASH> --session C:/path/x.session   # refresh 1 akun
```

## Next actions (kalau mau lanjut)

- [ ] Cek ulang `activePioneers` tiap bulan; kalau naik signifikan, evaluasi lagi
- [ ] Kalau proyek buka weekly drop untuk non-ambassador, tambahkan `weekly` ke default actions
- [ ] Kalau 60 hari tercapai (≈ Jan 2027), cek `/ecosystem/kyc/status` untuk akun utama saja

## Pelajaran yang perlu masuk skill

- Endpoint klaim bisa **gated** walau `/state` bilang `enabled: true` → selalu coba klaim 1x sebelum menulis klaim reward di README (kasus weekly drop LUXA)
- `render-card.py` bawaan skill: viewport 900 px memotong log panjang; salin + naikkan ke 4000 sebelum render run multi-akun
- Path session Telethon harus NATIVE (`C:/...`), bukan MSYS (`/c/...`) — kalau tidak, `sqlite3.OperationalError: unable to open database file`

#!/usr/bin/env python3
"""Holt Kursdaten für Nasdaq-100, S&P 500 und Russell 2000 und schreibt
public/data/prices.json und public/data/meta.json für den Minervini-Screener.

Quellen:
  S&P 500      Wikipedia (Tabelle "List of S&P 500 companies")
  Nasdaq-100   Wikipedia (Tabelle "Nasdaq-100")
  Russell 2000 iShares IWM Holdings (CSV). Ersatzweise universe/russell2000.txt
  Kurse        Yahoo Finance über die Python-Bibliothek yfinance

Einstellungen über Umgebungsvariablen (alle optional):
  OUT_DIR        Zielordner (Standard: public/data)
  MIN_PRICE      Mindestkurs in USD (Standard: 5)
  MIN_AVG_VOL    Mindest-Durchschnittsvolumen, 50 Tage, in Aktien (Standard: 100000)
  INDEXES        Komma-Liste aus SP500,NDX,R2000 (Standard: alle drei)
  R2000_URL      eigene Adresse für die Russell-2000-Liste
"""
import datetime as dt
import io
import json
import math
import os
import re
import sys
import time

import pandas as pd
import requests

UA = {"User-Agent": "Mozilla/5.0 (compatible; minervini-screener/1.0)"}
OUT_DIR = os.environ.get("OUT_DIR", "public/data")
MIN_PRICE = float(os.environ.get("MIN_PRICE", "5"))
MIN_AVG_VOL = float(os.environ.get("MIN_AVG_VOL", "100000"))
INDEXES = [x.strip() for x in os.environ.get("INDEXES", "SP500,NDX,R2000").split(",") if x.strip()]
R2000_URL = os.environ.get(
    "R2000_URL",
    "https://www.ishares.com/us/products/239710/ishares-russell-2000-etf/"
    "1467271812596.ajax?fileType=csv&fileName=IWM_holdings&dataType=fund",
)
KEEP = 260          # Handelstage, die gespeichert werden (die App braucht mindestens 253)
BATCH = 100         # Ticker pro Yahoo-Abruf
MIN_STOCKS = 300    # darunter wird der Lauf abgebrochen, damit keine kaputten Daten veröffentlicht werden
TICKER_RE = re.compile(r"^[A-Z]{1,5}(-[A-Z])?$")


def log(*a):
    print(*a, flush=True)


# ---------------------------------------------------------------- Indexlisten
def norm_ticker(t):
    t = str(t).strip().upper().replace(".", "-")
    return t if TICKER_RE.match(t) else None


def wiki_tables(url):
    r = requests.get(url, headers=UA, timeout=60)
    r.raise_for_status()
    return pd.read_html(io.StringIO(r.text))


def pairs(df, tcol, ncol):
    names = df[ncol] if ncol in df.columns else [""] * len(df)
    return [(norm_ticker(t), str(n).strip() if isinstance(n, str) else "") for t, n in zip(df[tcol], names)]


def universe_sp500():
    for t in wiki_tables("https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"):
        if "Symbol" in t.columns and len(t) > 400:
            return pairs(t, "Symbol", "Security")
    raise RuntimeError("Keine S&P-500-Tabelle gefunden")


def universe_ndx():
    for t in wiki_tables("https://en.wikipedia.org/wiki/Nasdaq-100"):
        if "Ticker" in t.columns and 80 <= len(t) <= 130:
            return pairs(t, "Ticker", "Company")
    raise RuntimeError("Keine Nasdaq-100-Tabelle gefunden")


def parse_ishares_csv(text):
    lines = text.splitlines()
    start = next((i for i, l in enumerate(lines) if l.lower().startswith("ticker,")), None)
    if start is None:
        raise RuntimeError("Kopfzeile 'Ticker' nicht gefunden")
    df = pd.read_csv(io.StringIO("\n".join(lines[start:])), on_bad_lines="skip")
    if "Asset Class" in df.columns:
        df = df[df["Asset Class"].astype(str).str.strip().str.lower() == "equity"]
    df = df.dropna(subset=["Ticker"])
    return [(norm_ticker(t), str(n).strip().title() if isinstance(n, str) else "")
            for t, n in zip(df["Ticker"], df["Name"] if "Name" in df.columns else [""] * len(df))]


def universe_r2000():
    try:
        r = requests.get(R2000_URL, headers=UA, timeout=90)
        r.raise_for_status()
        out = parse_ishares_csv(r.text)
        if len([x for x in out if x[0]]) < 1000:
            raise RuntimeError("zu wenige Zeilen in der iShares-Datei")
        return out
    except Exception as e:  # Ersatz: eigene Liste im Repository
        path = os.path.join(os.path.dirname(__file__), "..", "universe", "russell2000.txt")
        if os.path.exists(path):
            log("  iShares nicht lesbar (%s), nutze universe/russell2000.txt" % e)
            with open(path, encoding="utf-8") as f:
                return [(norm_ticker(x), "") for x in f.read().split()]
        raise


SOURCES = {"SP500": universe_sp500, "NDX": universe_ndx, "R2000": universe_r2000}


def build_universe():
    ix_map, status, names = {}, {}, {}
    for key in INDEXES:
        try:
            rows = [(t, n) for t, n in SOURCES[key]() if t]
            for t, n in rows:
                ix_map.setdefault(t, set()).add(key)
                if n and t not in names:      # Reihenfolge SP500, NDX, R2000: der erste Name gilt
                    names[t] = n
            status[key] = {"ok": True, "n": len(set(t for t, _ in rows))}
            log("  %s: %d Ticker" % (key, status[key]["n"]))
        except Exception as e:
            status[key] = {"ok": False, "error": str(e)[:200]}
            log("  %s: FEHLER %s" % (key, e))
    return ix_map, status, names


def fetch_fx():
    """USD je 1 EUR (Yahoo-Symbol EURUSD=X). Bei Fehler None, die App nutzt dann ihren eigenen Wert."""
    try:
        import yfinance as yf
        h = yf.Ticker("EURUSD=X").history(period="5d")["Close"].dropna()
        v = num(h.iloc[-1])
        return round(v, 4) if v and 0.5 < v < 2 else None
    except Exception as e:
        log("  Wechselkurs nicht abrufbar:", str(e)[:100])
        return None


# --------------------------------------------------------------------- Kurse
def split_batch(df, batch):
    """Teilt das Ergebnis von yf.download in ein Dict {Ticker: DataFrame}."""
    out = {}
    if df is None or df.empty:
        return out
    if isinstance(df.columns, pd.MultiIndex):
        lvl0 = set(df.columns.get_level_values(0))
        for t in batch:
            if t in lvl0:
                sub = df[t].dropna(how="all")
                if not sub.empty:
                    out[t] = sub
    elif len(batch) == 1:
        out[batch[0]] = df.dropna(how="all")
    return out


def download(tickers):
    import yfinance as yf

    raw, failed = {}, []
    for i in range(0, len(tickers), BATCH):
        batch = tickers[i:i + BATCH]
        got = {}
        for attempt in range(3):
            try:
                df = yf.download(batch, period="16mo", interval="1d", group_by="ticker",
                                 auto_adjust=False, threads=True, progress=False, timeout=30)
                got = split_batch(df, batch)
                if got:
                    break
            except Exception as e:
                log("  Abruf %d/%d fehlgeschlagen (%s)" % (attempt + 1, 3, str(e)[:80]))
            time.sleep(5 * (attempt + 1))
        raw.update(got)
        failed += [t for t in batch if t not in got]
        log("  %d/%d Ticker abgerufen" % (min(i + BATCH, len(tickers)), len(tickers)))
        time.sleep(1.5)
    return raw, failed


# ------------------------------------------------------------- Aufbereitung
def to_unix_day(ts):
    ts = pd.Timestamp(ts)
    if ts.tzinfo is not None:
        ts = ts.tz_localize(None)
    return int(ts.normalize().value // 86_400_000_000_000)


def num(x):
    try:
        f = float(x)
    except (TypeError, ValueError):
        return None
    return f if math.isfinite(f) else None


def assemble(raw, ix_map, names=None, min_price=MIN_PRICE, min_avg_vol=MIN_AVG_VOL, keep=KEEP):
    """Baut das Ausgabeformat. raw: {Ticker: DataFrame mit Close, High, Low, Volume}."""
    frames = {}
    for t, df in raw.items():
        if not {"Close", "High", "Low", "Volume"} <= set(df.columns):
            continue
        d = df.copy()
        d.index = [pd.Timestamp(x).tz_localize(None) if pd.Timestamp(x).tzinfo else pd.Timestamp(x) for x in d.index]
        d = d[~d.index.duplicated(keep="last")].sort_index()
        d = d.dropna(subset=["Close"])
        if len(d) >= 200:
            frames[t] = d
    if not frames:
        return None
    # gemeinsame Handelstage: die am häufigsten vorkommenden der letzten Zeit
    counts = {}
    for d in frames.values():
        for x in d.index[-keep - 5:]:
            counts[x] = counts.get(x, 0) + 1
    need = max(counts.values()) * 0.3
    dates = sorted(x for x, n in counts.items() if n >= need)[-keep:]
    last_day = dates[-1]
    stocks = []
    for t in sorted(frames):
        d = frames[t]
        if (last_day - d.index[-1]).days > 5:      # seit Tagen kein Kurs: ausgelistet oder Datenfehler
            continue
        close = d["Close"].reindex(dates)
        p = num(d["Close"].iloc[-1])
        w = d.iloc[-252:]
        vol_series = w["Volume"].dropna()
        av = num(d["Volume"].dropna().iloc[-50:].mean()) if len(vol_series) else None
        if p is None or p < min_price or av is None or av < min_avg_vol:
            continue
        if close.notna().sum() < 200:
            continue
        stocks.append({
            "t": t,
            "n": (names or {}).get(t, ""),
            "ix": sorted(ix_map.get(t, [])),
            "c": [None if num(v) is None else round(float(v), 2) for v in close],
            "p": round(p, 2),
            "hi": round(float(w["High"].max()), 2),
            "lo": round(float(w["Low"].min()), 2),
            "vol": int(num(d["Volume"].iloc[-1]) or 0),
            "av": int(av),
            "pe": None,
        })
    return {
        "generated": dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "asof": last_day.strftime("%Y-%m-%d"),
        "dates": [to_unix_day(x) for x in dates],
        "stocks": stocks,
    }


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    log("Indexlisten holen")
    ix_map, status, names = build_universe()
    tickers = sorted(ix_map)
    if not tickers:
        log("Keine Ticker gefunden, Abbruch.")
        return 1
    log("%d verschiedene Ticker, lade Kurse" % len(tickers))
    raw, failed = download(tickers)
    payload = assemble(raw, ix_map, names)
    if not payload or len(payload["stocks"]) < MIN_STOCKS:
        log("Nur %d Aktien aufbereitet (Minimum %d), Abbruch." % (len(payload["stocks"]) if payload else 0, MIN_STOCKS))
        return 1
    payload["failed"] = failed[:300]
    payload["fx"] = fetch_fx()
    with open(os.path.join(OUT_DIR, "prices.json"), "w", encoding="utf-8") as f:
        json.dump(payload, f, separators=(",", ":"))
    per_ix = {k: sum(1 for s in payload["stocks"] if k in s["ix"]) for k in INDEXES}
    meta = {"generated": payload["generated"], "asof": payload["asof"], "stocks": len(payload["stocks"]),
            "per_index": per_ix, "fx": payload["fx"], "sources": status, "failed": len(failed),
            "filters": {"min_price": MIN_PRICE, "min_avg_volume": MIN_AVG_VOL}}
    with open(os.path.join(OUT_DIR, "meta.json"), "w", encoding="utf-8") as f:
        json.dump(meta, f, indent=1)
    log("Fertig: %d Aktien, Stand %s, %s" % (len(payload["stocks"]), payload["asof"], per_ix))
    return 0


if __name__ == "__main__":
    sys.exit(main())

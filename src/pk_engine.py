# src/pk_engine.py
import os, json
from datetime import datetime, timedelta
from typing import List, Dict, Tuple
import numpy as np
import pandas as pd
import yfinance as yf
import psycopg2
from dotenv import load_dotenv
from src.progress import append_block

load_dotenv()

# ---------- DB ----------
def get_conn():
    return psycopg2.connect(os.getenv("DATABASE_URL"))

# ---------- Helpers ----------
def _to_scalar(val):
    """強制轉 float scalar"""
    if isinstance(val, (pd.Series, np.ndarray, list)):
        val = np.array(val).flatten()[0]
    return float(val)

def _to_series(x):
    """確保是單維度 Series"""
    if isinstance(x, pd.DataFrame):
        x = x.squeeze()  # 將 (N,1) DataFrame 轉為 Series
    return pd.Series(x).astype(float)

# ---------- Data ----------
def load_prices(symbol: str, period: str = "1y") -> pd.DataFrame:
    df = yf.download(symbol, period=period, interval="1d", auto_adjust=True, progress=False)
    df = df.dropna()
    df["Close"] = _to_series(df["Close"])  # 強制單維
    df["ret"] = df["Close"].pct_change().fillna(0.0)
    return df

# ---------- Indicators ----------
def ema(series: pd.Series, span: int) -> pd.Series:
    series = _to_series(series)
    return series.ewm(span=span, adjust=False).mean()

def rsi(series: pd.Series, window: int = 14) -> pd.Series:
    series = _to_series(series)
    delta = series.diff()
    up = np.where(delta > 0, delta, 0.0)
    down = np.where(delta < 0, -delta, 0.0)
    up_series = pd.Series(up, index=series.index)
    down_series = pd.Series(down, index=series.index)
    roll_up = up_series.rolling(window).mean()
    roll_down = down_series.rolling(window).mean()
    rs = roll_up / (roll_down.replace(0, np.nan))
    rsi = 100 - (100 / (1 + rs))
    return rsi.fillna(50.0)

# ---------- Metrics ----------
def max_drawdown(equity: pd.Series) -> float:
    equity = _to_series(equity)
    peak = equity.cummax()
    dd = (equity / peak) - 1.0
    mdd = dd.min()
    return _to_scalar(mdd * 100.0)

def total_return(equity: pd.Series) -> float:
    equity = _to_series(equity)
    start = _to_scalar(equity.iloc[0])
    end = _to_scalar(equity.iloc[-1])
    return (end / start - 1.0) * 100.0

def win_rate(trade_pnls: List[float]) -> float:
    clean = []
    for x in trade_pnls:
        try:
            clean.append(_to_scalar(x))
        except Exception:
            continue
    if not clean:
        return None
    wins = sum(1 for x in clean if x > 0)
    return (wins / len(clean)) * 100.0

# ---------- Backtests ----------
def bt_ma_crossover(df: pd.DataFrame, fast: int = 5, slow: int = 20) -> Tuple[pd.Series, List[float]]:
    px = _to_series(df["Close"])
    ema_fast = ema(px, fast)
    ema_slow = ema(px, slow)
    long_signal = (ema_fast > ema_slow).astype(int).fillna(0)

    pos = long_signal.shift(1).fillna(0)
    daily_ret = df["ret"] * pos
    equity = (1.0 + daily_ret).cumprod()

    trades = []
    in_pos = False
    entry_px = None

    for i in range(1, len(px)):
        prev_sig = int(_to_scalar(long_signal.iloc[i-1]))
        curr_sig = int(_to_scalar(long_signal.iloc[i]))
        if (not in_pos) and (prev_sig == 0) and (curr_sig == 1):
            in_pos = True
            entry_px = _to_scalar(px.iloc[i])
        elif in_pos and (prev_sig == 1) and (curr_sig == 0):
            exit_px = _to_scalar(px.iloc[i])
            trades.append(exit_px / entry_px - 1.0)
            in_pos = False

    if in_pos and entry_px is not None:
        exit_px = _to_scalar(px.iloc[-1])
        trades.append(exit_px / entry_px - 1.0)
    trades = [t * 100.0 for t in trades]
    return equity, trades

def bt_rsi_revert(df: pd.DataFrame, rsi_len: int = 14, buy_th: float = 30, sell_th: float = 50) -> Tuple[pd.Series, List[float]]:
    px = _to_series(df["Close"])
    r = rsi(px, rsi_len)
    pos = pd.Series(0, index=df.index)
    in_pos = False
    entry_px = None
    trades = []

    for i in range(1, len(px)):
        if not in_pos and r.iloc[i-1] < buy_th and r.iloc[i] >= buy_th:
            in_pos = True
            entry_px = _to_scalar(px.iloc[i])
            pos.iloc[i] = 1
        elif in_pos:
            pos.iloc[i] = 1
            if r.iloc[i-1] < sell_th and r.iloc[i] >= sell_th:
                exit_px = _to_scalar(px.iloc[i])
                trades.append((exit_px / entry_px - 1.0) * 100.0)
                in_pos = False
                pos.iloc[i] = 0

    daily_ret = df["ret"] * pos
    equity = (1.0 + daily_ret).cumprod()
    if in_pos and entry_px is not None:
        exit_px = _to_scalar(px.iloc[-1])
        trades.append((exit_px / entry_px - 1.0) * 100.0)
    return equity, trades

def bt_dca_monthly(df: pd.DataFrame, monthly_amt: float = 1000.0) -> Tuple[pd.Series, None]:
    px = _to_series(df["Close"])
    dates = df.index
    equity = []
    shares = 0.0
    last_month = None
    for i, d in enumerate(dates):
        if last_month != d.month:
            shares += monthly_amt / _to_scalar(px.iloc[i])
            last_month = d.month
        equity.append(shares * _to_scalar(px.iloc[i]))
    equity = pd.Series(equity, index=dates)
    return equity / _to_scalar(equity.iloc[0]), None

# ---------- Strategy Template ----------
def classify_template(style: str, core_claim: str, entry: str, exit: str) -> Dict:
    text = " ".join([core_claim or "", entry or "", exit or ""]).lower()
    if style == "short_term":
        if "ema" in text or "均線" in text or "ma" in text or "交叉" in text:
            return {"type": "ma", "fast": 5, "slow": 20}
        if "rsi" in text or "超買" in text or "超賣" in text:
            return {"type": "rsi", "rsi_len": 14, "buy": 30, "sell": 50}
        return {"type": "rsi", "rsi_len": 14, "buy": 30, "sell": 50}
    else:
        if "dca" in text or "逢低加碼" in text or "定期定額" in text or "分批" in text:
            return {"type": "dca"}
        return {"type": "dca"}

def backtest_template(df: pd.DataFrame, tpl: Dict) -> Tuple[float, float, float, List[float]]:
    if tpl["type"] == "ma":
        equity, trades = bt_ma_crossover(df, fast=tpl.get("fast", 5), slow=tpl.get("slow", 20))
    elif tpl["type"] == "rsi":
        equity, trades = bt_rsi_revert(df, rsi_len=tpl.get("rsi_len", 14), buy_th=tpl.get("buy", 30), sell_th=tpl.get("sell", 50))
    else:
        equity, trades = bt_dca_monthly(df)
    tr = total_return(equity)
    mdd = max_drawdown(equity)
    wr = win_rate(trades) if trades else None
    return tr, mdd, wr, trades or []

# ---------- Main PK ----------
def run_pk(symbols=("QQQ", "SPY"), period="1y", limit=10):
    conn = get_conn(); cur = conn.cursor()
    cur.execute("""
        SELECT id, style, core_claim, entry_rule, exit_rule
        FROM candidate_strategy
        WHERE is_strategy = TRUE
        ORDER BY analyzed_at DESC
        LIMIT %s;
    """, (limit,))
    rows = cur.fetchall()
    if not rows:
        print("⚠️ 沒有可回測的策略（is_strategy=TRUE）")
        conn.close()
        return

    price_cache = {sym: load_prices(sym, period) for sym in symbols}

    results = []
    for cid, style, core, entry, exit_ in rows:
        tpl = classify_template(style, core, entry, exit_)
        for sym in symbols:
            df = price_cache[sym]
            tr, mdd, wr, trades = backtest_template(df, tpl)
            summary = f"{tpl['type']} on {sym}: TR={tr:.2f}%, MDD={mdd:.2f}%"
            if wr is not None:
                summary += f", WR={wr:.1f}%"
            results.append((style, cid, sym, tr, mdd, wr, summary, tpl))

    winners = {}
    for style in ["short_term", "long_term"]:
        style_rows = [r for r in results if r[0] == style]
        if not style_rows:
            continue
        style_rows.sort(key=lambda x: (x[3], -x[4] if x[4] is not None else 0), reverse=True)
        winners[style] = style_rows[0]

    logs = []
    for style, cid, sym, tr, mdd, wr, summary, tpl in results:
        win_ref = winners.get(style)
        is_winner = win_ref and win_ref[1] == cid and win_ref[2] == sym
        rank = 1 if is_winner else None
        status = "winner" if is_winner else "loser"
        meta = {"template": tpl}
        cur.execute("""
            INSERT INTO pk_result
            (candidate_strategy_id, symbol_tested, period, total_return_pct, max_drawdown_pct, win_rate_pct, style, summary_for_host, rank_in_style, status, backtest_metadata)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s);
        """, (cid, sym, period, tr, mdd, wr, style, summary, rank, status, json.dumps(meta)))
        tag = "🏆" if is_winner else "•"
        logs.append(f"{tag} {str(cid)[:8]} [{style}] {sym} → TR {tr:.2f}% | MDD {mdd:.2f}% | WR {('n/a' if wr is None else f'{wr:.1f}%')} ({tpl['type']})")

    conn.commit(); conn.close()

    lines = ["Strategy PK Engine (period=1y)"] + logs
    for style, win in winners.items():
        _, cid, sym, tr, mdd, wr, summary, tpl = win
        lines.append(f"✅ Winner [{style}] {str(cid)[:8]} on {sym} — TR {tr:.2f}% / MDD {mdd:.2f}% / WR {('n/a' if wr is None else f'{wr:.1f}%')} ({tpl['type']})")

    append_block("Strategy PK Engine", lines)
    print("\n".join(lines))

if __name__ == "__main__":
    run_pk()

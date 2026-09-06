"""Convert a Fidelity account-history CSV into a simple realized gain/loss CSV.

FIFO matches buys against sells (either order, so short positions work too),
then combines every matched trade of the same stock/option into one row.

Usage:  python gain_loss.py History_for_Account_218320885.csv [gain_loss.csv]
"""

import csv
import io
import re
import sys
from collections import defaultdict, deque

# rows that never represent a trade
SKIP_ACTION = re.compile(
    r"DIVIDEND|REINVESTMENT|JOURNALED|ROLLOVER|REDEMPTION|INTEREST|"
    r"TRANSFER|DEPOSIT|WITHDRAWAL|FEE|MERGER|IN LIEU",
    re.I,
)
CASH_SYMBOLS = {"SPAXX", "FDRXX", "FZFXX", "FCASH", "FDIC"}

FIELDS = ("stock", "gain/loss", "shares", "buy price", "sell price",
          "buy total", "sell total", "date buy", "date sell", "option")

# option symbols look like "-NFLX260618C99": underlying, expiry, C/P, strike
OPTION_RE = re.compile(r"^-([A-Z]+)(\d{2})(\d{2})(\d{2})([CP])([\d.]+)$")


def num(s):
    s = (s or "").strip().replace(",", "").replace("$", "")
    if not s:
        return 0.0
    return float(s)


def read_trades(path):
    """Yield (date, symbol, signed_qty, cash) for real buys/sells, oldest first."""
    lines = open(path, encoding="utf-8-sig").read().splitlines()
    start = next(i for i, l in enumerate(lines) if l.startswith("Run Date"))
    trades = []
    for r in csv.DictReader(io.StringIO("\n".join(lines[start:]))):
        date = (r.get("Run Date") or "").strip()
        if not re.match(r"\d\d/\d\d/\d{4}$", date):
            continue  # trailing disclaimer text
        action = re.sub(r"\s+", " ", (r.get("Action") or "").strip())
        symbol = (r.get("Symbol") or "").strip()
        qty = num(r.get("Quantity"))
        if not symbol or symbol in CASH_SYMBOLS or not qty:
            continue
        if SKIP_ACTION.search(action):
            continue
        # Amount is already net of commission and fees; it is 0 for an
        # expired/assigned option leg, which simply closes the position.
        cash = num(r.get("Amount ($)"))
        trades.append((date, symbol, qty, cash))
    trades.reverse()  # file is newest-first
    return trades


def expiry(m):
    """Expiration date of a matched option symbol, as MM/DD/YYYY."""
    return "%s/%s/20%s" % (m.group(3), m.group(4), m.group(2))


def match_fifo(trades, report_date):
    """Return closed trades: (key, shares, buy_total, sold_total, buy_date, sell_date).

    key is (symbol, round): the round counter bumps every time the position goes
    flat, so buying a stock again after selling it all starts a fresh row.
    """
    lots = defaultdict(deque)  # symbol -> [qty, unit_cash, date]
    rounds = defaultdict(int)
    closed = []
    for date, symbol, qty, cash in trades:
        unit = abs(cash) / abs(qty)
        key = (symbol, rounds[symbol])
        while qty and lots[symbol] and (lots[symbol][0][0] > 0) != (qty > 0):
            lot = lots[symbol][0]
            n = min(abs(lot[0]), abs(qty))
            if lot[0] > 0:  # long lot closed by this sell
                closed.append((key, n, n * lot[1], n * unit, lot[2], date))
            else:  # short lot closed by this buy
                closed.append((key, n, n * unit, n * lot[1], date, lot[2]))
            lot[0] -= n if lot[0] > 0 else -n
            qty -= -n if qty < 0 else n
            if lot[0] == 0:
                lots[symbol].popleft()
        if qty:
            lots[symbol].append([qty, unit, date])
        if not lots[symbol]:
            rounds[symbol] += 1  # position flat; anything after this is a new row

    # an option still open past its expiration was never traded out: it expired
    # worthless, which closes it at $0 on the expiration date
    for symbol, lot_q in lots.items():
        m = OPTION_RE.match(symbol)
        if not m or not lot_q or key_date(expiry(m)) > key_date(report_date):
            continue
        key = (symbol, rounds[symbol])
        for qty, unit, date in lot_q:
            n = abs(qty)
            if qty > 0:  # long option: premium paid is lost
                closed.append((key, n, n * unit, 0.0, date, expiry(m)))
            else:  # short option: premium collected is kept
                closed.append((key, n, 0.0, n * unit, expiry(m), date))
        lot_q.clear()

    open_pos = {s: l for s, l in lots.items() if l}
    return closed, open_pos


def combine(closed):
    """One row per stock/option."""
    agg = {}
    for key, shares, buy_total, sold_total, buy_date, sell_date in closed:
        a = agg.setdefault(key, [0.0, 0.0, 0.0, buy_date, sell_date])
        a[0] += shares
        a[1] += buy_total
        a[2] += sold_total
        a[3] = min(a[3], buy_date, key=key_date)
        a[4] = max(a[4], sell_date, key=key_date)
    rows = []
    for (symbol, _), (shares, buy_total, sold_total, buy_date, sell_date) in agg.items():
        rows.append(row(symbol, shares, buy_total / shares, buy_date,
                        sold_total / shares, sell_date,
                        gain=sold_total - buy_total))
    return sort_rows(rows)


def still_open(open_pos):
    """One row per position left open at the end: no gain/loss yet."""
    rows = []
    for symbol, lots in open_pos.items():
        shares = sum(l[0] for l in lots)
        unit = sum(abs(l[0]) * l[1] for l in lots) / abs(shares)
        date = min((l[2] for l in lots), key=key_date)
        if shares > 0:  # bought, not sold yet
            rows.append(row(symbol, shares, unit, date, "", "", gain=""))
        else:  # sold short, or bought before this history file starts
            rows.append(row(symbol, shares, "", "", unit, date, gain=""))
    return sort_rows(rows)


def row(symbol, shares, buy_price, buy_date, sell_price, sell_date, gain):
    m = OPTION_RE.match(symbol)
    per = 100 if m else 1  # option prices are quoted per underlying share
    return {
        "stock": m.group(1) if m else symbol,
        "gain/loss": round(gain, 2) if gain != "" else "",
        "shares": round(shares, 4),
        "buy price": round(buy_price / per, 2) if buy_price != "" else "",
        "sell price": round(sell_price / per, 2) if sell_price != "" else "",
        "buy total": round(buy_price * abs(shares), 2) if buy_price != "" else "",
        "sell total": round(sell_price * abs(shares), 2) if sell_price != "" else "",
        "date buy": buy_date,
        "date sell": sell_date,
        "option": symbol if m else "",
    }


def sort_rows(rows):
    """Newest activity first: the later of the two dates on the row."""
    rows.sort(key=lambda r: max(key_date(d) for d in (r["date buy"], r["date sell"]) if d),
              reverse=True)
    return rows


def key_date(d):
    m, dd, y = d.split("/")
    return (y, m, dd)


def main():
    src = sys.argv[1] if len(sys.argv) > 1 else "History_for_Account_218320885.csv"
    dst = sys.argv[2] if len(sys.argv) > 2 else "gain_loss.csv"

    trades = read_trades(src)
    closed, open_pos = match_fifo(trades, report_date=trades[-1][0])
    open_rows = still_open(open_pos)
    closed_rows = combine(closed)
    total = sum(r["gain/loss"] for r in closed_rows)

    with open(dst, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(FIELDS))
        w.writeheader()
        w.writerows(open_rows)  # still-open positions first
        w.writerows(closed_rows)
        w.writerow({"stock": "TOTAL", "gain/loss": round(total, 2)})

    print("%s: %d closed positions, total gain/loss %.2f; %d still open"
          % (dst, len(closed_rows), total, len(open_rows)))


if __name__ == "__main__":
    main()

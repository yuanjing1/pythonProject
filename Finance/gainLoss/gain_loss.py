"""Convert a Fidelity account-history CSV into a simple realized gain/loss CSV.

FIFO matches buys against sells (either order, so short positions work too),
then combines the matched trades of the same stock/option sold in the same
year into one row.

Usage:  python gain_loss.py [X65750304 ...]

Reads ../data/History_for_Account_<account>.csv and writes ../data/gain_loss_<account>.csv.
With no account given, every history file in ../data is processed.
"""

import csv
import glob
import io
import os
import re
import sys
from collections import defaultdict, deque

# default files live in ../data relative to this script, not in the current directory
DATA = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
HISTORY = "History_for_Account_%s.csv"

# rows that never represent a trade
SKIP_ACTION = re.compile(
    r"DIVIDEND|REINVESTMENT|JOURNALED|ROLLOVER|REDEMPTION|INTEREST|"
    r"TRANSFER|DEPOSIT|WITHDRAWAL|FEE|MERGER|IN LIEU",
    re.I,
)
CASH_SYMBOLS = {"SPAXX", "FDRXX", "FZFXX", "FCASH", "FDIC"}

FIELDS = ("stockOption", "shares", "buy price", "sell price",
          "buy total", "sell total", "gain/loss", "date buy", "date sell", "stock")

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


def download_date(path, trades):
    """Date the history file was downloaded, as MM/DD/YYYY.

    Fidelity dates pending ("Processing") rows on the next business day, so the
    latest trade date can be later than today; the download date is the real
    as-of date. Falls back to the latest trade date if the footer is missing.
    """
    m = re.search(r"Date downloaded (\d\d/\d\d/\d{4})",
                  open(path, encoding="utf-8-sig").read())
    return m.group(1) if m else trades[-1][0]


def expiry(m):
    """Expiration date of a matched option symbol, as MM/DD/YYYY."""
    return "%s/%s/20%s" % (m.group(3), m.group(4), m.group(2))


def match_fifo(trades, report_date):
    """Return (closed, open_pos, presold).

    closed trades: (key, shares, buy_total, sold_total, buy_date, sell_date).
    key is (symbol, round): the round counter bumps every time the position goes
    flat, so buying a stock again after selling it all starts a fresh row.

    presold: shares sold with no shares on hand. They were bought before this
    history file starts (e.g. called away), not sold short, so later buys must
    not close them: symbol -> [(qty, unit_cash, date)].
    """
    lots = defaultdict(deque)  # symbol -> [qty, unit_cash, date]
    rounds = defaultdict(int)
    closed = []
    presold = defaultdict(list)
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
        if qty < 0 and not OPTION_RE.match(symbol):
            presold[symbol].append((qty, unit, date))
        elif qty:
            lots[symbol].append([qty, unit, date])
        if not lots[symbol]:
            rounds[symbol] += 1  # position flat; anything after this is a new row

    # an option still open past its expiration was never traded out: it expired
    # worthless, which closes it at $0 on the expiration date. An option expiring
    # on report_date itself can still trade that day, so it stays open.
    for symbol, lot_q in lots.items():
        m = OPTION_RE.match(symbol)
        if not m or not lot_q or key_date(expiry(m)) >= key_date(report_date):
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
    return closed, open_pos, presold


def combine(closed):
    """One row per stock/option per year sold."""
    agg = {}
    for key, shares, buy_total, sold_total, buy_date, sell_date in closed:
        year = key_date(sell_date)[0]
        a = agg.setdefault(key + (year,), [0.0, 0.0, 0.0, buy_date, sell_date])
        a[0] += shares
        a[1] += buy_total
        a[2] += sold_total
        a[3] = min(a[3], buy_date, key=key_date)
        a[4] = max(a[4], sell_date, key=key_date)
    rows = []
    for (symbol, _, _), (shares, buy_total, sold_total, buy_date, sell_date) in agg.items():
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
        else:  # option sold to open
            rows.append(row(symbol, shares, "", "", unit, date, gain=""))
    # grouped by underlying, the share row first and then that stock's options
    rows.sort(key=lambda r: (r["stock"], r["stockOption"] != r["stock"], r["stockOption"]))
    return rows


def sold_presold(presold):
    """Sales of shares bought before this history file: cost basis unknown."""
    return [row(symbol, -qty, "", "", unit, date, gain="")
            for symbol, sales in presold.items() for qty, unit, date in sales]


def row(symbol, shares, buy_price, buy_date, sell_price, sell_date, gain):
    m = OPTION_RE.match(symbol)
    per = 100 if m else 1  # option prices are quoted per underlying share
    return {
        "stockOption": symbol,  # option symbol, or the ticker for shares
        "gain/loss": round(gain, 2) if gain != "" else "",
        "shares": round(shares),
        # buys are cash out, so shown negative ("or 0.0" avoids printing -0.0)
        "buy price": round(-buy_price / per, 2) or 0.0 if buy_price != "" else "",
        "sell price": round(sell_price / per, 2) if sell_price != "" else "",
        "buy total": round(-buy_price * abs(shares), 2) or 0.0 if buy_price != "" else "",
        "sell total": round(sell_price * abs(shares), 2) if sell_price != "" else "",
        "date buy": buy_date,
        "date sell": sell_date,
        "stock": m.group(1) if m else symbol,  # underlying ticker
    }


def sort_rows(rows):
    """Newest activity first: the later of the two dates on the row."""
    rows.sort(key=lambda r: max(key_date(d) for d in (r["date buy"], r["date sell"]) if d),
              reverse=True)
    return rows


def key_date(d):
    m, dd, y = d.split("/")
    return (y, m, dd)


def accounts():
    """Every account with a history file in data/."""
    pattern = os.path.join(DATA, HISTORY % "*")
    head, tail = HISTORY.split("%s")
    return sorted(os.path.basename(p)[len(head):-len(tail)] for p in glob.glob(pattern))


def run(account):
    src = os.path.join(DATA, HISTORY % account)
    dst = os.path.join(DATA, "gain_loss_%s.csv" % account)
    if not os.path.exists(src):
        sys.exit("no history file for account %s: %s" % (account, src))

    trades = read_trades(src)
    closed, open_pos, presold = match_fifo(trades, report_date=download_date(src, trades))
    open_rows = still_open(open_pos)
    closed_rows = sort_rows(combine(closed) + sold_presold(presold))
    total = sum(r["gain/loss"] for r in closed_rows if r["gain/loss"] != "")

    with open(dst, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(FIELDS))
        w.writeheader()
        w.writerows(open_rows)  # still-open positions first
        w.writerows(closed_rows)
        w.writerow({"stockOption": "TOTAL", "gain/loss": round(total, 2)})

    print("%s: %d closed positions, total gain/loss %.2f; %d still open"
          % (dst, len(closed_rows), total, len(open_rows)))


def main():
    todo = sys.argv[1:] or accounts()
    if not todo:
        sys.exit("no history files in %s" % DATA)
    for account in todo:
        run(account)


if __name__ == "__main__":
    main()

"""strategy comparison — chart + summary table
S1  Hold 100 shares 
S2  sell (covered call) + buy (LEAPS/deep ITM call): Diagonal / poor man's covered call
S3  sell (covered call) + sell put: Covered straddle
"""

import numpy as np
import matplotlib.pyplot as plt

# ---------------------------------------------------------------- parameters
COST_BASIS    = 498 # also used as the reference spot on the chart

LEAPS_STRIKE  = 330 # AMD270917C330
LEAPS_PRICE   = 208

CALL_PRICE    = 18         
PUT_PRICE     = 19

MULT          = 100         # contract multiplier, and the share count

# chart and table span the strikes, padded so both kinks sit inside the picture
PAD       = 0.30                                    # fraction beyond the outer strike
STRIKE_LO = min(LEAPS_STRIKE, COST_BASIS)
STRIKE_HI = max(LEAPS_STRIKE, COST_BASIS)
PRICE_LO  = max(STRIKE_LO * (1 - PAD), 0.0)
PRICE_HI  = STRIKE_HI * (1 + PAD)

PRICES = np.arange(PRICE_LO, PRICE_HI + 1, 1.0)


# ------------------------------------------------------------------ payoffs
def s1(S):
    """Hold 100 shares."""
    return MULT * (S - COST_BASIS)


def s2(S):
    """LEAPS"""
    debit = (LEAPS_PRICE - CALL_PRICE) * MULT          # 19,900
    return MULT * np.maximum(S - LEAPS_STRIKE, 0.0) - debit


def s3(S):
    """Covered straddle"""
    stock = MULT * (S - COST_BASIS)
    call = MULT * (CALL_PRICE - np.maximum(S - COST_BASIS, 0.0))
    put = MULT * (PUT_PRICE - np.maximum(COST_BASIS - S, 0.0))
    return stock + call + put


STRATEGIES = {                      # escape any \$ you add: matplotlib reads $..$ as math
    r"S1  Hold 100 shares":      (s1, "#64748b"),
    r"S2  LEAPS":           (s2, "#2563eb"),
    r"S3  Covered straddle": (s3, "#dc2626"),
}


# ------------------------------------------------------------------- metrics
def breakevens(fn, ref=None, grid=PRICES):
    """Prices where fn crosses zero, or crosses ref when one is given."""
    y = fn(grid) if ref is None else fn(grid) - ref(grid)
    idx = np.where(np.diff(np.sign(y)))[0]
    hits = []
    for i in idx:
        if y[i + 1] == y[i]:
            continue
        b = round(float(grid[i] - y[i] * (grid[i + 1] - grid[i])
                        / (y[i + 1] - y[i])), 2)
        if not hits or abs(b - hits[-1]) > 1e-6:   # zero touched exactly
            hits.append(b)
    return hits


def summary_table():
    sample = sorted({PRICE_LO, LEAPS_STRIKE, COST_BASIS, PRICE_HI}   # interesting prices
                    | {b for fn, _ in STRATEGIES.values()
                       for b in breakevens(fn)})
    head = ["Metric"] + [n.split()[0] for n in STRATEGIES]
    rows = [head,
            ["Max loss (-> 0)"] + [f"{fn(0.0):,.0f}" for fn, _ in STRATEGIES.values()],
            ["Breakeven"] + [", ".join(f"{b:,.2f}" for b in breakevens(fn)) or ""
                             for fn, _ in STRATEGIES.values()],
            ["Compare with Hold"] + [", ".join(f"{b:,.2f}" for b in breakevens(fn, s1))
                                   or "" for fn, _ in STRATEGIES.values()]]
    last_metric = len(rows) - 1                    # blank line goes after this row
    for S in sample:
        tag = f"{S:,.0f}" if float(S).is_integer() else f"{S:,.2f}"
        rows.append([f"P/L at ${tag}"] +
                    [f"{fn(float(S)):,.0f}" for fn, _ in STRATEGIES.values()])

    width = [max(len(r[c]) for r in rows) for c in range(len(head))]
    out = []
    for i, r in enumerate(rows):
        out.append("  ".join(c.rjust(w) if j else c.ljust(w)
                             for j, (c, w) in enumerate(zip(r, width))))
        if i == 0:
            out.append("  ".join("-" * w for w in width))
        elif i == last_metric:                     # blank line before the P/L rows
            out.append("")
    return "\n".join(out)


# --------------------------------------------------------------------- plot
# where each curve carries its own label: (fraction along PRICES, y-offset pt)
LABEL_POS = {"S1": (0.35, 12), "S2": (0.72, -12), "S3": (0.22, -12)}


def plot():
    fig, ax = plt.subplots(figsize=(11, 6.5))

    for label, (fn, color) in STRATEGIES.items():
        y = fn(PRICES)
        ax.plot(PRICES, y, color=color, lw=2, label=label)
        frac, dy = LABEL_POS[label.split()[0]]
        x = PRICES[0] + frac * (PRICES[-1] - PRICES[0])
        ax.annotate(label, xy=(x, float(fn(x))),
                    xytext=(0, dy), textcoords="offset points",
                    color=color, fontsize=9, fontweight="bold", ha="center",
                    va="bottom" if dy > 0 else "top",
                    bbox=dict(boxstyle="round,pad=0.25", fc="white",
                              ec="none", alpha=0.75))

    ax.axhline(0, color="#94a3b8", lw=0.9)
    ax.axvline(COST_BASIS, color="#0f172a", lw=0.9, ls=":")
    ax.annotate(rf"cost basis \${COST_BASIS:,.2f}", xy=(COST_BASIS, ax.get_ylim()[1]),
                xytext=(4, -14), textcoords="offset points",
                fontsize=9, color="#0f172a")

    ax.axvline(LEAPS_STRIKE, color="#cbd5e1", lw=0.8, ls="--", zorder=0)

    ax.set_xlabel("share price ($)")
    ax.set_ylabel("Profit / Loss ($)")
    ax.set_title("strategy comparison")
    ax.yaxis.set_major_formatter(lambda v, _: f"{v:,.0f}")
    ax.grid(alpha=0.25)
    ax.set_xlim(PRICES[0], PRICES[-1])
    fig.tight_layout()
    plt.show()
    return fig


if __name__ == "__main__":
    print(summary_table(), "\n")
    plot()
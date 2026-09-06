"""
AMD strategy comparison — payoff chart + summary table.

S1  Hold 100 shares @ $477
S2  Diagonal / poor man's covered call:
      long  AMD 2027-09-17 C300 @ $214
      short AMD 2026-09-16 C480 @ $15
S3  Covered straddle:
      100 shares + short AMD 2026-09-16 C480 @ $15
                 + short AMD 2026-09-16 P480 @ $18

Payoffs are drawn at expiry (each option taken to intrinsic). For S2 the short
call dies in Sep-2026 while the LEAPS runs to Sep-2027, so the curve assumes the
call expires worthless and the premium is banked -- true whenever AMD < 480 on
2026-09-16. See mark_s2_at_short_expiry() for the model-marked alternative.
"""

import numpy as np
import matplotlib.pyplot as plt

# ---------------------------------------------------------------- parameters
SHARES        = 100
COST_BASIS    = 477.00      # also used as the reference spot on the chart

LEAPS_STRIKE  = 300.0       # AMD270917C300
LEAPS_PRICE   = 214.00

CALL_STRIKE   = 480.0       # AMD260916C480
CALL_PRICE    = 15.00

PUT_STRIKE    = 480.0       # AMD260916P480
PUT_PRICE     = 18.00

MULT          = 100         # contract multiplier
RATE          = 0.04
LEAPS_IV      = 0.5929      # backed out from $214 at 477
T_LEAPS       = 376 / 365   # to 2027-09-17
T_CALL        = 10 / 365    # to 2026-09-16

PRICES = np.arange(250, 600, 1.0)


# ------------------------------------------------------------------ payoffs
def s1(S):
    """Hold 100 shares."""
    return SHARES * (S - COST_BASIS)


def s2(S):
    """Diagonal: long LEAPS call, short near-dated call. No stock."""
    debit = (LEAPS_PRICE - CALL_PRICE) * MULT          # 19,900
    return MULT * np.maximum(S - LEAPS_STRIKE, 0.0) - debit


def s3(S):
    """Covered straddle: shares, short call and short put at the same strike."""
    stock = SHARES * (S - COST_BASIS)
    call = MULT * (CALL_PRICE - np.maximum(S - CALL_STRIKE, 0.0))
    put = MULT * (PUT_PRICE - np.maximum(PUT_STRIKE - S, 0.0))
    return stock + call + put


STRATEGIES = {                                   # \$ so matplotlib skips mathtext
    r"S1  100 shares @ \$477":                   (s1, "#64748b"),
    r"S2  diagonal: +300C \$214 / -480C \$15":   (s2, "#2563eb"),
    r"S3  shares -480C \$15 -480P \$18":         (s3, "#dc2626"),
}


# ------------------------------------------------- optional: mark S2 on 9/16
def _bs_call(S, K, T, sigma, r=RATE):
    from scipy.stats import norm
    d1 = (np.log(S / K) + (r + 0.5 * sigma ** 2) * T) / (sigma * np.sqrt(T))
    return S * norm.cdf(d1) - K * np.exp(-r * T) * norm.cdf(d1 - sigma * np.sqrt(T))


def mark_s2_at_short_expiry(S):
    """S2 valued on 2026-09-16, LEAPS still carrying ~1 year of time value."""
    T = T_LEAPS - T_CALL
    leaps = MULT * (_bs_call(S, LEAPS_STRIKE, T, LEAPS_IV) - LEAPS_PRICE)
    call = MULT * (CALL_PRICE - np.maximum(S - CALL_STRIKE, 0.0))
    return leaps + call


# ------------------------------------------------------------------- metrics
def breakevens(fn, grid=PRICES):
    y = fn(grid)
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


SAMPLE_OFFSETS = (-100, -50, 0, 50, 100)   # sample points around COST_BASIS


def summary_table(sample=None):
    if sample is None:
        sample = [COST_BASIS + d for d in SAMPLE_OFFSETS]
    head = ["Metric"] + [n.split()[0] for n in STRATEGIES]
    rows = [head,
            ["Max loss (AMD -> 0)"] + [f"{fn(0.0):,.0f}" for fn, _ in STRATEGIES.values()],
            ["Breakeven"] + [", ".join(f"{b:,.2f}" for b in breakevens(fn)) or "n/a"
                             for fn, _ in STRATEGIES.values()]]
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
        elif i == 2:                               # blank line after breakeven
            out.append("")
    return "\n".join(out)


# --------------------------------------------------------------------- plot
def plot():
    fig, ax = plt.subplots(figsize=(11, 6.5))

    for label, (fn, color) in STRATEGIES.items():
        y = fn(PRICES)
        ax.plot(PRICES, y, color=color, lw=2, label=label)
        ax.annotate(label.split()[0], xy=(PRICES[-1], y[-1]),
                    xytext=(6, 0), textcoords="offset points",
                    color=color, fontsize=10, fontweight="bold",
                    va="center", ha="left", clip_on=False)

    ax.axhline(0, color="#94a3b8", lw=0.9)
    ax.axvline(COST_BASIS, color="#0f172a", lw=0.9, ls=":")
    ax.annotate(rf"cost basis \${COST_BASIS:,.2f}", xy=(COST_BASIS, ax.get_ylim()[1]),
                xytext=(4, -14), textcoords="offset points",
                fontsize=9, color="#0f172a")

    for K in (LEAPS_STRIKE, CALL_STRIKE):
        ax.axvline(K, color="#cbd5e1", lw=0.8, ls="--", zorder=0)

    ax.set_xlabel("AMD share price at expiry ($)")
    ax.set_ylabel("Profit / Loss ($)")
    ax.set_title("AMD strategy comparison — payoff at expiry")
    ax.yaxis.set_major_formatter(lambda v, _: f"{v:,.0f}")
    ax.grid(alpha=0.25)
    ax.legend(loc="upper left", fontsize=9, frameon=False)
    ax.set_xlim(PRICES[0], PRICES[-1] + 25)
    fig.tight_layout()
    plt.show()
    return fig


if __name__ == "__main__":
    print(summary_table(), "\n")
    plot()
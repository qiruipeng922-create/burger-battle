"""Q2: 30-day Monte Carlo for the strategy panel, with true random tie-breaking.

Cash below 4 coins is absorbing (a closed day leaves cash unchanged), so "ruin"
means the shop can never trade again; a "zombie" is a strategy that is still
closed on day 30 because it chose/needed to stay under its threshold.

Run:  python3 q2_simulation.py            (4000 seeds x 30 days per matchup)
"""
import os
import random
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from engine import DAYS, cost, max_afford, simulate_day  # noqa: E402

SEEDS = 4000
DAYS_IN_GAME = 30


def fixed(price, stock, close_below=0):
    """buy `stock` burgers at `price`, down-scaling if cash is short"""
    def f(cash, history):
        ma = max_afford(cash)
        # ma == 0 means the cash covers the opening fee but no burger on top
        # (cash in [4, 6)); opening just to sell nothing would burn 4 coins,
        # so the shop stays closed instead of following the fallback literally
        if cash < 4 or cash < close_below or ma == 0:
            return None
        return price, min(stock, ma)
    return f


def aggressive(price):
    """buy as many burgers as the cash allows (the 'umbrella breaker')"""
    def f(cash, history):
        ma = max_afford(cash)
        if cash < 4 or ma == 0:
            return None
        return price, ma
    return f


def adaptive(base_price=6, fallback_price=4, stock=4, trigger=8):
    """play the one-day optimum, but drop the price for good once the rival is
    seen stockpiling more than `trigger` burgers (history is public)"""
    state = {"switch": False}

    def f(cash, history):
        seen = max([h[1] for h in history] or [0])          # rival stock observed so far
        if seen > trigger:
            state["switch"] = True
        ma = max_afford(cash)
        if cash < 4 or ma == 0:
            return None
        return (fallback_price if state["switch"] else base_price), min(stock, ma)
    return f


def dual_adaptive(base_price=6, safe_price=4, stock=4, trigger=8, low_cash=18):
    """Dual-threshold safe adaptive strategy (E+):
    1. Cash buffer defense: if cash <= low_cash, switch to safe 4@4 (zero downside
       risk on quiet days) until cash recovers above low_cash.
    2. Rival defense: if rival ever stockpiles > trigger burgers, drop to 4@4 permanently."""
    state = {"rival_alert": False}

    def f(cash, history):
        seen = max([h[1] for h in history] or [0])
        if seen > trigger:
            state["rival_alert"] = True
        ma = max_afford(cash)
        if cash < 4 or ma == 0:
            return None
        p = safe_price if (state["rival_alert"] or cash <= low_cash) else base_price
        return p, min(stock, ma)
    return f


# strategies are factories: every simulated path gets a fresh instance, so a
# stateful rule (the adaptive price switch) never leaks across paths
MINE = {
    "A 4@6": lambda: fixed(6, 4),
    "B 4@4": lambda: fixed(4, 4),
    "C 8@4": lambda: fixed(4, 8),
    "D 4@6 stop<12": lambda: fixed(6, 4, close_below=12),
    "E adaptive": lambda: adaptive(),
    "E+ dual-safe": lambda: dual_adaptive(),
}
RIVALS = {
    "R1 cautious 4@4": lambda: fixed(4, 4),
    "R2 mirror 4@6": lambda: fixed(6, 4),
    "R3 aggressive 8@4": lambda: fixed(4, 8),
    "R4 undercut 4@3": lambda: fixed(3, 4),
    "R5 premium 4@8": lambda: fixed(8, 4),
    "R6 stockpiler @4": lambda: aggressive(4),
    "R7 flood @6": lambda: aggressive(6),
}


def play(mine_factory, rival_factory, seed):
    rnd = random.Random(seed)
    mine, rival = mine_factory(), rival_factory()
    cash = [30.0, 30.0]
    sold = [0, 0]
    hist_mine, hist_rival = [], []
    traded_last = [False, False]
    surplus = 0.0          # student surplus accumulated over the path
    unmet = 0.0            # customers who left without a burger
    for _ in range(DAYS_IN_GAME):
        _, D, w = DAYS[rnd.randrange(3)]
        d1 = mine(cash[0], hist_rival)          # I see the rival's past, not today
        d2 = rival(cash[1], hist_mine)
        p = [x[0] if x else 0 for x in (d1, d2)]
        q = [x[1] if x else 0 for x in (d1, d2)]
        s = simulate_day(p, q, [d1 is not None, d2 is not None], w, D, rnd)
        traded_last = [d1 is not None, d2 is not None]
        for i, d in enumerate((d1, d2)):
            if d is not None:
                cash[i] += -4 - cost(d[1]) + d[0] * s[i]
                sold[i] += s[i]
                surplus += s[i] * max(0.0, w - d[0])
        unmet += D - (s[0] + s[1])
        hist_mine.append((p[0], q[0]))
        hist_rival.append((p[1], q[1]))
    return cash, sold, traded_last, surplus, unmet


def evaluate(mine, rival, seeds=SEEDS):
    tot_cash = tot_sold = ruin = stopped = 0.0
    for s in range(seeds):
        cash, sold, traded, _, _ = play(mine, rival, 31337 + 7 * s)
        tot_cash += cash[0]
        tot_sold += sold[0]
        ruin += cash[0] < 4
        stopped += not traded[0]
    return tot_cash / seeds, 100 * ruin / seeds, 100 * stopped / seeds, tot_sold / seeds


def evaluate_welfare(mine, rival, seeds=SEEDS):
    """same runs, reporting what the students got out of the match"""
    surplus = sold = unmet = cash = 0.0
    for s in range(seeds):
        c, sd, _, cs, un = play(mine, rival, 31337 + 7 * s)
        surplus += cs
        sold += sd[0] + sd[1]
        unmet += un
        cash += c[0] + c[1]
    return {"cs": surplus / seeds, "burgers": sold / seeds,
            "unmet": unmet / seeds, "shop_cash": cash / seeds}


def main():
    print(f"30-day Monte Carlo, {SEEDS} paths per matchup, true random tie-breaking\n")
    head = "my strategy".ljust(18) + "".join(f"{r.split()[0]:>8}" for r in RIVALS)
    print(head)
    results = {}
    for mname, mine in MINE.items():
        row = f"{mname:<18}"
        for rname, rival in RIVALS.items():
            cash, ruin, stopped, sold = evaluate(mine, rival)
            results[(mname, rname)] = (cash, ruin, stopped, sold)
            row += f"{cash:8.1f}"
        print(row)
    print("\nruin probability (%), same layout")
    print(head)
    for mname in MINE:
        print(f"{mname:<18}" + "".join(f"{results[(mname, r)][1]:8.1f}" for r in RIVALS))
    print("\nburgers sold by my shop, same layout")
    print(head)
    for mname in MINE:
        print(f"{mname:<18}" + "".join(f"{results[(mname, r)][3]:8.0f}" for r in RIVALS))
    print("\nnot trading on day 30 (%, ruin plus voluntary permanent closure)")
    print(head)
    for mname in MINE:
        print(f"{mname:<18}" + "".join(f"{results[(mname, r)][2]:8.1f}" for r in RIVALS))
    print("\nrival's own final cash and ruin rate")
    for rname, rival in RIVALS.items():
        cash = ruin = 0.0
        for s in range(SEEDS):
            c, _, _, _, _ = play(MINE["A 4@6"], rival, 31337 + 7 * s)
            cash += c[1]
            ruin += c[1] < 4
        print(f"  {rname:<20} final cash {cash/SEEDS:6.1f}   ruin {100*ruin/SEEDS:5.1f}%")

    print("\n30-day welfare of selected matchups (cumulative over the 30 days)")
    print(f"  {'matchup':<22}{'student surplus':>16}{'burgers sold':>14}{'unmet demand':>14}{'shops cash':>12}")
    for mn, rn in [("A 4@6", "R1 cautious 4@4"), ("A 4@6", "R6 stockpiler @4"),
                   ("E adaptive", "R6 stockpiler @4"), ("B 4@4", "R1 cautious 4@4"),
                   ("C 8@4", "R3 aggressive 8@4"), ("D 4@6 stop<12", "R1 cautious 4@4")]:
        w = evaluate_welfare(MINE[mn], RIVALS[rn], seeds=1000)
        print(f"  {mn + ' vs ' + rn.split()[0]:<22}{w['cs']:16.0f}{w['burgers']:14.0f}"
              f"{w['unmet']:14.0f}{w['shop_cash']:12.0f}")
    return results


if __name__ == "__main__":
    main()

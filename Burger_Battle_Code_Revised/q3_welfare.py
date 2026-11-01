"""Q3: student welfare under different competitive outcomes.

1. exact per-day consumer surplus, burgers sold and unmet demand for named profiles
2. the same quantities for every one of the 39 weak Nash equilibria of the one-day game
3. 30-day welfare aggregates from the Q2 simulation
Run:  python3 q3_welfare.py
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from engine import DAYS, cost, day_expect, max_afford  # noqa: E402


def profile(me, rival, days=1):
    """(consumer surplus, burgers sold, unmet demand, shop profit) per day, both shops"""
    p1, q1, o1 = me
    p2, q2, o2 = rival
    cs = sold = unmet = profit = demand = 0.0
    for _, D, w in DAYS:
        a, b, s1, s2, c = day_expect(p1, q1, o1, p2, q2, o2, D, w)
        cs += c / 3
        sold += (s1 + s2) / 3
        profit += (a + b) / 3
        demand += D / 3
    return cs * days, sold * days, (demand - sold) * days, profit * days


def openp(q, p):
    return (p, q, True)


CLOSED = (0, 0, False)

NAMED = [
    ("monopoly, 4 @ 4", openp(4, 4), CLOSED),
    ("monopoly, 4 @ 6", openp(4, 6), CLOSED),
    ("duopoly, symmetric (4@6, 4@6)", openp(4, 6), openp(4, 6)),
    ("duopoly, asymmetric (4@4, 4@6)", openp(4, 4), openp(4, 6)),
    # the best equilibrium for students; kept at index 4 so that NAMED[:5] below
    # reproduces exactly the first five rows of Table 6 in the report
    ("duopoly, best equilibrium (6@6, 6@4)", openp(6, 6), openp(6, 4)),
    ("duopoly, (4@4, 8@6)", openp(4, 4), openp(8, 6)),
    ("duopoly, price war (8@1, 8@1)", openp(8, 1), openp(8, 1)),
    ("duopoly, both cautious (4@4, 4@4)", openp(4, 4), openp(4, 4)),
]


def weak_equilibria():
    """recompute the 73 x 73 payoff matrix and return the weak pure Nash pairs"""
    S = [("close", 0, None)] + [("open", q, p) for q in range(9) for p in range(1, 9)
                                if 4 + cost(q) <= 30]
    dec = [(p if a == "open" else 0, q, a == "open") for a, q, p in S]
    n = len(S)
    M = [[sum(day_expect(dec[i][0], dec[i][1], dec[i][2],
                         dec[j][0], dec[j][1], dec[j][2], D, w)[0]
              for _, D, w in DAYS) / 3 for j in range(n)] for i in range(n)]
    colmax = [max(c) for c in zip(*M)]
    pairs = [(i, j) for i in range(n) for j in range(n)
             if abs(M[i][j] - colmax[j]) < 1e-9 and abs(M[j][i] - colmax[i]) < 1e-9]
    return dec, pairs, M


def main():
    print("1. per-day welfare of named profiles (average over the three day types)")
    print(f"{'profile':<34}{'CS':>8}{'burgers':>9}{'unmet':>8}{'shop profit':>13}")
    for name, me, rival in NAMED:
        cs, sold, unmet, prof = profile(me, rival)
        print(f"{name:<34}{cs:8.2f}{sold:9.2f}{unmet:8.2f}{prof:13.2f}")

    print("\n   over 30 days (the fixed plans repeated, for comparison):")
    # NOTE: "shops" here is total profit over the 30 days. Table 6 of the report
    # shows "shops' final coins", i.e. this profit plus the 30 starting coins
    # each shop began with (e.g. monopoly 4@4: 120 profit -> 150 final coins).
    for name, me, rival in NAMED[:5]:
        cs, sold, unmet, prof = profile(me, rival, days=30)
        print(f"   {name:<34} CS {cs:7.0f}  burgers {sold:6.0f}  unmet {unmet:6.0f}  shops {prof:7.0f}")

    print("\n2. student surplus in each of the weak Nash equilibria of the one-day game")
    dec, pairs, M = weak_equilibria()
    rows = []
    for i, j in pairs:
        cs, sold, unmet, prof = profile(dec[i], dec[j])
        rows.append((cs, sold, unmet, prof, dec[i], dec[j]))
    rows.sort()
    print(f"   {len(rows)} equilibria, every one pays the two shops {rows[0][3]:+.2f} "
          f"in total, i.e. {rows[0][3] / 2:+.2f} each")
    print(f"   student surplus ranges {rows[0][0]:.2f} .. {rows[-1][0]:.2f} per day, "
          f"burgers {rows[0][1]:.2f} .. {rows[-1][1]:.2f}")
    print(f"   worst for students: ({rows[0][4][1]}@{rows[0][4][0]}, {rows[0][5][1]}@{rows[0][5][0]})"
          f"  CS {rows[0][0]:.2f}")
    print(f"   best  for students: ({rows[-1][4][1]}@{rows[-1][4][0]}, {rows[-1][5][1]}@{rows[-1][5][0]})"
          f"  CS {rows[-1][0]:.2f}")
    mid = rows[len(rows) // 2]
    print(f"   median equilibrium: CS {mid[0]:.2f}, shops {mid[3]:+.2f} each")


if __name__ == "__main__":
    main()

"""Q1 evidence: complete enumeration of the one-day game.

This script produces every number quoted in Section 1 of the report:

  * Table 1   five candidate plans, per day type and in expectation
  * Table 2   the two "sweet spots" under the monopoly benchmark and in competition
  * Table 3   worst case of "buy 4 @ 6" as the rival's maximum stock grows
  *           the +4.00 ceiling of the whole 73 x 73 payoff matrix
  *           the 39 weak pure Nash equilibria (and the absence of strict ones)
  *           the unique maximin plan
  *           the parameter sensitivity quoted in Section 1.5

Run:  python3 q1_enumeration.py      (a few seconds, no third-party packages)
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from engine import DAYS, cost, day_expect, max_afford  # noqa: E402


def op(q, p):
    return (p, q, True)


CLOSED = (0, 0, False)
BENCH = op(4, 4)                 # the cautious benchmark rival of the report


def daily(me, rival):
    """(profit per day type, expected profit) of one shop against a rival plan"""
    p1, q1, o1 = me
    p2, q2, o2 = rival
    per = [day_expect(p1, q1, o1, p2, q2, o2, D, w)[0] for _, D, w in DAYS]
    return per, sum(per) / 3


def feasible():
    """the 73 plans available on the first day: closing, or q in 0..8 and p in 1..8"""
    out = [("close", CLOSED)]
    for q in range(9):
        for p in range(1, 9):
            if 4 + cost(q) <= 30:
                out.append((f"q={q}, p={p}", op(q, p)))
    return out


def table1():
    print("Table 1 - five candidate plans against the benchmark rival (4 @ 4)")
    print(f"  {'plan':<14}{'quiet':>9}{'normal':>9}{'festival':>10}{'expected':>10}")
    for q, p in [(4, 4), (4, 6), (8, 6), (6, 4), (8, 4)]:
        per, exp = daily(op(q, p), BENCH)
        print(f"  {f'buy {q} @ {p}':<14}{per[0]:9.2f}{per[1]:9.2f}{per[2]:10.2f}{exp:10.2f}")
    print("  (the four extra MegaGrill burgers of buy 8 @ 4 cost 16 coins and add 2.71 sales)")


def ceiling_and_equilibria():
    S = feasible()
    M = [[daily(me, riv)[1] for _, riv in S] for _, me in S]
    n = len(S)
    print(f"\nceiling - {n} feasible plans, {n * n} matchups")
    print(f"  highest entry of the whole payoff matrix: {max(max(r) for r in M):+.2f}")
    best = max(((sum(day_expect(p, q, True, 0, 0, False, D, w)[0] for _, D, w in DAYS) / 3, q, p)
                for q in range(13) for p in range(1, 9)), key=lambda t: t[0])
    print(f"  best monopoly profit over the unrestricted grid q <= 12: {best[0]:+.2f} "
          f"(at q={best[1]}, p={best[2]})")
    for q in (4, 6, 8, 12):
        mono = sum(day_expect(6, q, True, 0, 0, False, D, w)[0] for _, D, w in DAYS) / 3
        print(f"    monopoly with p = 6, q = {q:2d}: {mono:+.2f}  "
              f"(marginal burger costs 4, sells with probability 2/3, earns 6 x 2/3 = 4)")
    colmax = [max(c) for c in zip(*M)]
    weak = [(i, j) for i in range(n) for j in range(n)
            if abs(M[i][j] - colmax[j]) < 1e-9 and abs(M[j][i] - colmax[i]) < 1e-9]
    strict = [(i, j) for i, j in weak
              if sum(abs(M[i][k] - colmax[j]) < 1e-9 for k in range(n)) == 1
              and sum(abs(M[k][j] - colmax[i]) < 1e-9 for k in range(n)) == 1]
    print(f"\nequilibria of the one-day game")
    print(f"  weak pure Nash equilibria: {len(weak)}, each paying both shops "
          f"{M[weak[0][0]][weak[0][1]]:+.2f}")
    print(f"  strict equilibria: {len(strict)}")
    worst = sorted(((min(M[i][j] for j in range(n)), S[i][0]) for i in range(n)), reverse=True)
    print(f"  maximin (best worst case): {worst[0][1]} with {worst[0][0]:+.2f}; "
          f"runner-up {worst[1][1]} with {worst[1][0]:+.2f}")
    print("  symmetric play, price ladder (both shops choose the same plan):")
    for q in (4, 6):
        row = "  ".join(f"p{p}:{daily(op(q, p), op(q, p))[1]:+.2f}" for p in range(1, 9))
        print(f"    q = {q}:  {row}")


def table3_robustness():
    print("\nTable 3 - worst case of buy 4 @ 6 as the rival's stock grows")
    closed = daily(op(4, 6), CLOSED)[1]
    print(f"  rival closed: {closed:+.2f}")
    for rq in (4, 6, 8, 9, 10, 12):
        vals = [(daily(op(4, 6), op(rq, rp))[1], rp) for rp in range(1, 9)]
        worst, price = min(vals)
        cash = 4 + cost(rq)
        print(f"  rival stock {rq:2d} (needs {cash:2d} coins): worst {worst:+.2f} "
              f"at rival price {price}")


def sensitivity():
    """re-solve the one-day problem under the parameter changes quoted in Section 1.5"""
    print("\nsensitivity of the one-day optimum (monopoly benchmark)")

    def best(fee=4, quiet=4, normal=6):
        days = [("Quiet", 6, quiet), ("Normal", 12, normal), ("Festival", 18, 8)]
        out = []
        for q in range(13):
            if fee + cost(q) > 30:
                continue
            for p in range(1, 9):
                v = sum((p * (min(D, q) if p <= w else 0) - cost(q) - fee) / 3 for _, D, w in days)
                out.append((v, q, p))
        v, q, p = max(out)
        return v, q, p, [x for x in out if abs(x[0] - v) < 1e-9]

    for label, kw in [("baseline", {}), ("opening fee 6", {"fee": 6}),
                      ("quiet-day cap 5", {"quiet": 5}), ("normal-day cap 5", {"normal": 5})]:
        v, q, p, ties = best(**kw)
        plans = ", ".join(f"buy {t[1]} @ {t[2]}" for t in ties[:3]) + (" ..." if len(ties) > 3 else "")
        print(f"  {label:<18} value {v:+.2f}   optimal plans: {plans}")


def worked_example():
    print("\nworked example of the problem statement (both shops buy 4, charge 4)")
    for name, D, w in DAYS:
        pr, _, s1, s2, _ = day_expect(4, 4, True, 4, 4, True, D, w)
        print(f"  {name:<9} safe {D:2d} customers: expected sales {s1:.3f} each, "
              f"expected profit {pr:+.3f} each")
    print(f"  day-one affordable stock: {max_afford(30)} burgers")


if __name__ == "__main__":
    worked_example()
    table1()
    ceiling_and_equilibria()
    table3_robustness()
    sensitivity()

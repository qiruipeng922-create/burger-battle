"""Assert every number quoted in q1_section_revised.md. Prints PASS/FAIL per claim."""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from engine import DAYS, cost, day_expect, max_afford  # noqa: E402

ok = fail = 0


def check(label, got, want, tol=5e-3):
    global ok, fail
    if abs(got - want) <= tol:
        ok += 1
        print(f"  PASS  {label}: {got:+.4f}")
    else:
        fail += 1
        print(f"  FAIL  {label}: got {got:+.4f}, section says {want:+.4f}")


def per_day(p, q, rp, rq, rival_open=True):
    return [day_expect(p, q, True, rp, rq, rival_open, D, w)[0] for _, D, w in DAYS]


def exp_profit(p, q, rp, rq, rival_open=True):
    return sum(per_day(p, q, rp, rq, rival_open)) / 3


def sold(p, q, rp, rq, day_index):
    _, D, w = DAYS[day_index]
    return day_expect(p, q, True, rp, rq, True, D, w)[2]


print("Table 1 (benchmark rival 4 @ 4):")
for (q, p), want in [((4, 4), 2.67), ((4, 6), 4.00), ((8, 6), 4.00), ((6, 4), 0.17), ((8, 4), -2.50)]:
    check(f"expected profit {q}@{p}", exp_profit(p, q, 4, 4), want, 0.005)
check("quiet profit 4@4", per_day(4, 4, 4, 4)[0], 0.0)
check("quiet profit 4@6", per_day(6, 4, 4, 4)[0], -12.0)
check("normal profit 4@6", per_day(6, 4, 4, 4)[1], 12.0)
check("quiet profit 8@6", per_day(6, 8, 4, 4)[0], -28.0)
check("normal profit 8@6", per_day(6, 8, 4, 4)[1], 20.0)
check("quiet profit 6@4", per_day(4, 6, 4, 4)[0], -7.5)
check("quiet profit 8@4", per_day(4, 8, 4, 4)[0], -15.5)
check("quiet sales of 8@4 (burgers, not coins)", sold(4, 8, 4, 4, 0), 3.125)
extra = sum(sold(4, 8, 4, 4, d) - sold(4, 4, 4, 4, d) for d in range(3)) / 3
check("extra sales/day of 8@4 over 4@4", extra, 2.71, 0.005)

print("\nSection 1.4 upper bound:")
grid = [exp_profit(p, q, 0, 0, rival_open=False) for q in range(0, 13) for p in range(1, 9)]
check("best monopoly profit, full grid q<=12", max(grid), 4.0)
check("monopoly profit 4@7", exp_profit(7, 4, 0, 0, False), -2.6667, 0.01)
for q in (4, 5, 6, 8, 12):
    check(f"monopoly profit {q}@6", exp_profit(6, q, 0, 0, False), 4.0)
for q in (4, 5, 6):
    check(f"monopoly profit {q}@4", exp_profit(4, q, 0, 0, False), 4.0)

print("\nSection 1.5 / Table 2:")
check("monopoly 4@4", exp_profit(4, 4, 0, 0, False), 4.0)
check("monopoly 6@4", exp_profit(4, 6, 0, 0, False), 4.0)
check("8@6 against a rival playing 6@6", exp_profit(6, 8, 6, 6), 1.16, 0.01)
check("4@4 against benchmark", exp_profit(4, 4, 4, 4), 2.67, 0.005)
check("6@4 against benchmark", exp_profit(4, 6, 4, 4), 0.17, 0.005)
check("4@6 against benchmark", exp_profit(6, 4, 4, 4), 4.0)
check("8@6 against benchmark", exp_profit(6, 8, 4, 4), 4.0)

print("\nTable 3 sensitivity (monopoly benchmark, affordable set only):")


def best(open_fee=4, quiet_wtp=4, normal_wtp=6):
    days = [("Quiet", 6, quiet_wtp), ("Normal", 12, normal_wtp), ("Festival", 18, 8)]
    best_v, best_plan = -99, None
    for q in range(0, 13):
        if open_fee + cost(q) > 30:
            continue
        for p in range(1, 9):
            v = sum((p * (min(D, q) if p <= w else 0) - cost(q) - open_fee) / 3 for _, D, w in days)
            if v > best_v + 1e-9:
                best_v, best_plan = v, (q, p)
    return best_v, best_plan


v, plan = best()
check("baseline best value", v, 4.0)
print(f"        (baseline argmax {plan}, e.g. any q>=4 @ 6)")
v, plan = best(open_fee=6)
check("opening fee 6: best value", v, 2.0)
opt6 = [(q, p) for q in range(0, 13) for p in range(1, 9)
        if 6 + cost(q) <= 30
        and abs(sum((p * (min(D, q) if p <= w else 0) - cost(q) - 6) / 3
                    for _, D, w in [("Quiet", 6, 4), ("Normal", 12, 6), ("Festival", 18, 8)]) - 2.0) < 1e-9]
check("opening fee 6: (6,6) is optimal", 1.0 if (6, 6) in opt6 else 0.0, 1.0)
print(f"        (opening fee 6: all optimal plans {sorted(opt6)})")
v, plan = best(quiet_wtp=5)
check("quiet cap 5: best value", v, 10.0)
check("quiet cap 5: argmax stock", plan[0], 6)
check("quiet cap 5: argmax price", plan[1], 5)
v, plan = best(normal_wtp=5)
check("normal cap 5: best value", v, 4.0)
check("normal cap 5: argmax stock", plan[0], 4)
check("normal cap 5: argmax price", plan[1], 4)

print("\nTable 4 (worst case of 4@6 by rival stock):")
for rq, want in [(0, 4.0), (4, 4.0), (6, 4.0), (8, 4.0), (9, 2.0), (10, 0.0), (12, -4.0)]:
    got = exp_profit(6, 4, 0, 0, False) if rq == 0 else min(exp_profit(6, 4, rp, rq) for rp in range(1, 9))
    check(f"rival stock {rq}", got, want, 0.005)
for rq in (9, 10, 12):
    worst = min(range(1, 9), key=lambda rp: exp_profit(6, 4, rp, rq))
    check(f"worst rival price at stock {rq} is 1 coin", worst, 1)
for q, need in [(9, 32), (10, 36), (12, 44)]:
    check(f"cash needed to stock {q}", 4 + cost(q), need)

print("\nSection 1.3 statements about Figure 1 (benchmark rival 4@4):")


def col(p):
    return [exp_profit(p, q, 4, 4) for q in range(1, 9)]


touching = [p for p in range(1, 9) if any(abs(v - 4.0) < 1e-9 for v in col(p))]
check("number of price columns that touch +4.00", len(touching), 1)
check("the column that touches +4.00 is p = 6", touching[0], 6)
check("p = 6 is flat at +4.00 for every q >= 4", min(col(6)[3:]), 4.0)
check("p = 4 peaks at +2.67", max(col(4)), 2.6667, 0.005)
check("p = 4 peak is at q = 4", 1 + col(4).index(max(col(4))), 4)
check("p = 4 negative for q >= 7", max(col(4)[6:]), -1.17, 0.01)
check("p = 7 negative at every stock", max(col(7)), -2.6667, 0.01)
check("p = 8 negative at every stock", max(col(8)), -1.3333, 0.01)

print("\nSection 1.7 (equilibria, day-one feasible set):")
S = [("close", 0, None)] + [("open", q, p) for q in range(9) for p in range(1, 9) if 4 + cost(q) <= 30]
dec = [(p if a == "open" else 0, q, a == "open") for a, q, p in S]
N = len(S)
M = [[sum(day_expect(dec[i][0], dec[i][1], dec[i][2], dec[j][0], dec[j][1], dec[j][2], D, w)[0]
           for _, D, w in DAYS) / 3 for j in range(N)] for i in range(N)]
colmax = [max(c) for c in zip(*M)]
weak = [(i, j) for i in range(N) for j in range(N)
        if abs(M[i][j] - colmax[j]) < 1e-9 and abs(M[j][i] - colmax[i]) < 1e-9]
strict = [(i, j) for i, j in weak
          if sum(abs(M[i][k] - colmax[j]) < 1e-9 for k in range(N)) == 1
          and sum(abs(M[k][j] - colmax[i]) < 1e-9 for k in range(N)) == 1]
check("number of feasible plans", N, 73)
check("weak equilibria", len(weak), 39)
check("strict equilibria", len(strict), 0)
check("all weak equilibria give +4.00", min(M[i][j] for i, j in weak), 4.0)
gains = sorted((min(M[i][j] for j in range(N)), i) for i in range(N))
check("maximin guarantee (best worst case)", gains[-1][0], 4.0)
check("runner-up guarantee", gains[-2][0], 2.0)
check("global matrix maximum", max(max(r) for r in M), 4.0)
check("stock affordable on day one", max_afford(30), 8)

print(f"\n{ok} passed, {fail} failed")
sys.exit(1 if fail else 0)

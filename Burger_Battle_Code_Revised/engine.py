"""Shared day-level model for the Burger Battle (HKUST(GZ) 2026 MCM Junior).

Every other script in this archive imports from here, so the demand model, the
cost function and the customer simulation are defined in exactly one place.

Contents
  DAYS            the three day types: (name, customers, willingness to pay)
  cost(q)         purchase cost: 2 coins for the first 4 burgers, 4 thereafter
  max_afford(c)   largest stock affordable with c coins on hand
  tie_sales(D,q1,q2)  expected sales of each shop at equal prices
  day_expect(...) exact expected profit / sales / surplus for one day type
  day_value(...)  the same averaged over the three day types
  simulate_day(...) stochastic version used by the 30-day simulation

Self-test:  python3 engine.py

Pure standard library (no numpy needed). Three checks:
  Q1  exact enumeration of the one-day game  (payoff ceiling, Nash set, maximin)
  Q2  30-day stochastic Monte Carlo           (ruin risk, adaptive rules)
  Q3  student-welfare accounting              (surplus + availability)

Rules encoded exactly as in the problem statement:
  days: Quiet 6 customers WTP 4 | Normal 12 WTP 6 | Festival 18 WTP 8, each 1/3
  cost: opening 4; LittleFlame first 4 units @2, then MegaGrill @4 up to 8 more
  cash: opening cost + purchase <= cash at start of day; cash < 4 -> must close
        (closed day leaves cash unchanged, so cash < 4 is an absorbing, i.e. final, state)
  customers: sequentially take the cheapest open shop that has stock and price <= WTP;
        on a tie the shop is chosen at random; if it is sold out they may try the other.
Run:  python3 engine.py
"""
import random
from math import comb

DAYS = [("Quiet", 6, 4), ("Normal", 12, 6), ("Festival", 18, 8)]


def cost(q):
    """purchase cost: 2/unit for the first 4, 4/unit afterwards (max 12 units/day)"""
    if q <= 0:
        return 0
    return 2 * q if q <= 4 else 8 + 4 * (q - 4)


def max_afford(cash):
    for q in range(12, -1, -1):
        if 4 + cost(q) <= cash:
            return q
    return 0


# ---------------------------------------------------------------- day engines
def tie_sales(D, q1, q2):
    """expected units sold by each shop when both charge the SAME affordable price.
    Customers split Binomial(D, 1/2) and the one who finds their shop empty walks to
    the other shop, so sold_i = min(x_i,q_i) + min(max(0,x_j-q_j), q_i - min(x_i,q_i))."""
    s1 = s2 = 0.0
    for x1 in range(D + 1):
        p = comb(D, x1) * 0.5 ** D
        x2 = D - x1
        a, b = min(x1, q1), min(x2, q2)
        s1 += p * (a + min(max(0, x2 - q2), q1 - a))
        s2 += p * (b + min(max(0, x1 - q1), q2 - b))
    return s1, s2


def day_expect(p1, q1, o1, p2, q2, o2, D, w):
    """(profit1, profit2, sold1, sold2, student_surplus) for one day type"""
    if not o1:
        q1, p1 = 0, None
    if not o2:
        q2, p2 = 0, None
    if o1 and o2:
        if p1 < p2:
            s1 = min(D, q1) if p1 <= w else 0
            s2 = min(D - s1, q2) if (q2 > 0 and p2 <= w) else 0
        elif p2 < p1:
            s2 = min(D, q2) if p2 <= w else 0
            s1 = min(D - s2, q1) if (q1 > 0 and p1 <= w) else 0
        else:
            s1, s2 = tie_sales(D, q1, q2) if p1 <= w else (0, 0)
    elif o1:
        s1 = min(D, q1) if p1 <= w else 0
        s2 = 0
    elif o2:
        s2 = min(D, q2) if p2 <= w else 0
        s1 = 0
    else:
        s1 = s2 = 0
    pr1 = (p1 * s1 - cost(q1) - 4) if o1 else 0.0
    pr2 = (p2 * s2 - cost(q2) - 4) if o2 else 0.0
    cs = s1 * max(0, w - (p1 or 0)) + s2 * max(0, w - (p2 or 0))
    return pr1, pr2, s1, s2, cs


def day_value(p1, q1, o1, p2, q2, o2):
    """expected per-day (profit1, sold1, student_surplus) averaged over the three day types"""
    P = S = C = 0.0
    for _, D, w in DAYS:
        a, _, s1, _, cs = day_expect(p1, q1, o1, p2, q2, o2, D, w)
        P += a / 3
        S += s1 / 3
        C += cs / 3
    return P, S, C


def simulate_day(prices, stocks, opens, w, D, rnd):
    """stochastic version used in the 30-day simulation (random tie-breaking)"""
    stock, sold = list(stocks), [0, 0]
    live = [i for i in range(2) if opens[i] and stock[i] > 0 and prices[i] <= w]
    for _ in range(D):
        cand = [i for i in live if stock[i] > 0]
        if not cand:
            break
        best = min(prices[i] for i in cand)
        cand = [i for i in cand if prices[i] == best]
        c = cand[0] if len(cand) == 1 else rnd.choice(cand)
        stock[c] -= 1
        sold[c] += 1
    return sold

if __name__ == "__main__":
    # the worked example of the problem statement: both shops buy 4 and charge 4
    for name, D, w in DAYS:
        pr, _, s1, s2, _ = day_expect(4, 4, True, 4, 4, True, D, w)
        print(f"{name:<9} D={D:2d}  expected sales per shop {s1:.3f} / {s2:.3f}  "
              f"expected profit per shop {pr:+.3f}")
    print("quiet-day profit is zero, matching the worked example:", 
          abs(day_expect(4,4,True,4,4,True,6,4)[0]) < 1e-12)

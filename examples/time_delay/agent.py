"""Agents with exponential and hyperbolic discounting."""

import math


def agent_exponential(x1, t1, x2, t2):
    """An agent who discounts expoentially."""
    discount_factor = 0.02
    v1 = x1 * math.exp(-discount_factor * t1)
    v2 = x2 * math.exp(-discount_factor * t2)

    return v1 > v2


def agent_hyperbolic(x1, t1, x2, t2):
    """An agent who discounts hyperbolically."""
    discount_factor = 0.05
    v1 = x1 / (1.0 + discount_factor * t1)
    v2 = x2 / (1.0 + discount_factor * t2)

    return v1 > v2

"""Conditional Bayesian limits for differences of independent binomial rates."""
from dataclasses import dataclass
from math import exp, log, log1p
from numbers import Integral

import numpy as np
from scipy.integrate import quad
from scipy.optimize import brentq, minimize_scalar
from scipy.special import betainc, betaincc, betaln, gammaln, logsumexp, xlog1py, xlogy


@dataclass(frozen=True)
class UpperLimit:
    observed_difference: float
    positive_probability: float
    log_positive_probability: float
    upper_limit: float
    conditional_probability: float
    max_relative_quadrature_error: float
    integrand_evaluations: int
    root_iterations: int


def posterior_parameters(on_hits, on_trials, off_hits, off_trials):
    for hits, trials in ((on_hits, on_trials), (off_hits, off_trials)):
        if (not isinstance(hits, Integral) or not isinstance(trials, Integral)
                or not 0 <= hits <= trials or trials == 0):
            raise ValueError("Each side requires integer counts with 0 <= hits <= trials and trials > 0")
    return (on_hits + 1, on_trials - on_hits + 1), (off_hits + 1, off_trials - off_hits + 1)


def log_density(p, a, b, normalizer):
    return xlogy(a - 1, p) + xlog1py(b - 1, -p) - normalizer


def difference_density(d, on, off):
    """Direct convolution for illustration and independent validation."""
    if abs(d) >= 1:
        return 0.0
    on_norm, off_norm = betaln(*on), betaln(*off)
    return quad(lambda p: exp(log_density(p + d, *on, on_norm) +
                              log_density(p, *off, off_norm)),
                max(0, -d), min(1, 1 - d), epsabs=1e-11)[0]


class DifferenceTail:
    def __init__(self, on, off):
        self.on = on
        self.off = off
        self.off_norm = betaln(*off)
        self.max_relative_error = 0.0
        self.evaluations = 0

    def log_survival(self, p, complement):
        if complement <= 0:
            return -np.inf
        a, b = self.on
        sf = betaincc(a, b, p) if p < .5 else betainc(b, a, complement)
        if sf > 1e-280:
            return log(sf)
        # Integer Beta survival equals P(Bin(a+b-1,p) <= a-1).
        # Sum the exact finite series in log space if the special function underflows.
        n = a + b - 1
        k = np.arange(a)
        return logsumexp(gammaln(n + 1) - gammaln(k + 1) - gammaln(n - k + 1)
                         + xlogy(k, p) + xlogy(n - k, complement))

    def log_tail(self, d):
        if d >= 1:
            return -np.inf
        end = 1 - d

        def integrand_log(p):
            return log_density(p, *self.off, self.off_norm) + self.log_survival(p + d, end - p)

        # Beta shapes are >= 1. The density and survival are log-concave,
        # so the product has a single mode (possibly at an endpoint).
        optimum = minimize_scalar(lambda p: -integrand_log(p), bounds=(0, end),
                                  method="bounded", options={"xatol": 1e-14})
        if not optimum.success:
            raise ArithmeticError("Could not locate posterior tail integrand mode")
        mode = max((0, optimum.x, end), key=integrand_log)
        peak = integrand_log(mode)

        def scaled(p):
            return exp(integrand_log(p) - peak)

        # Place breakpoints at the shoulders so adaptive quadrature sees
        # narrow peaks, including those adjacent to a domain boundary.
        def shoulder(p):
            return integrand_log(p) - peak + 35

        points = [mode]
        for boundary in (0, end):
            if shoulder(boundary) < 0:
                lo, hi = sorted((mode, boundary))
                points.append(brentq(shoulder, lo, hi, xtol=1e-15))
        result = quad(scaled, 0, end, points=sorted({point for point in points if 1e-13 * end < point < (1 - 1e-13) * end}),
                      epsabs=0, epsrel=1e-8, full_output=True)
        value, error, info = result[:3]
        if len(result) != 3 or not np.isfinite(peak) or value <= 0 or error / value > 1e-8:
            raise ArithmeticError("Posterior tail quadrature did not converge")
        self.max_relative_error = max(self.max_relative_error, error / value)
        self.evaluations += info["neval"]
        return peak + log(value)


def binomial_upper_limit(on_hits, on_trials, off_hits, off_trials, credible_level=0.95):
    """Return the posterior quantile conditional on a positive difference."""
    if not 0 < credible_level < 1:
        raise ValueError("Credible level must be strictly between zero and one")
    on, off = posterior_parameters(on_hits, on_trials, off_hits, off_trials)
    tail = DifferenceTail(on, off)
    positive = tail.log_tail(0)
    target = log1p(-credible_level)

    def residual(d):
        return tail.log_tail(d) - positive - target

    # Choose a nearby bracket first to avoid evaluating irrelevant far tails.
    mean = on[0] / sum(on) - off[0] / sum(off)
    variance = sum(a * b / (sum((a, b)) ** 2 * (a + b + 1)) for a, b in (on, off))
    high = min(1.0, max(mean, 0) + 5 * variance ** .5)
    while residual(high) > 0:
        high = min(1.0, 2 * high)
    upper, root = brentq(residual, 0, high, xtol=1e-14, full_output=True)
    conditional = -np.expm1(tail.log_tail(upper) - positive)
    if abs(conditional - credible_level) > 1e-8 or positive > 1e-8:
        raise ArithmeticError("Computed quantile does not attain the requested posterior mass")
    return UpperLimit(on_hits / on_trials - off_hits / off_trials, exp(min(positive, 0)),
                      min(positive, 0), upper, conditional, tail.max_relative_error,
                      tail.evaluations, root.iterations)

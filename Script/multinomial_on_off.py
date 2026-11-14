"""Signed likelihood ratio for equality of two multinomial weighted means."""
from dataclasses import dataclass
import numpy as np
from scipy.optimize import brentq
from scipy.special import xlogy

ROOT_TOL = 2e-14
FEAS_TOL = 2e-9
TS_TOL = 1e-8


@dataclass
class WeightedFit:
    score: float
    ts: float
    null_probabilities: np.ndarray
    iterations: int
    mean_gap: float


def fit_weighted_on_off(on, off, weights):
    counts = np.asarray([on, off], dtype=float)
    w = np.asarray(weights, dtype=float)
    if (w.ndim != 1 or not w.size or counts.shape != (2, w.size)
            or not np.isfinite(w).all() or np.ptp(w) <= 0
            or not np.isfinite(counts).all() or (counts < 0).any()
            or (counts != np.floor(counts)).any()):
        raise ValueError("Expected nonnegative integer counts and finite nonconstant weights")
    w = (w - w.min()) / np.ptp(w)
    totals = counts.sum(axis=1)
    if (totals == 0).any():
        return WeightedFit(np.nan, np.nan, np.full_like(counts, np.nan), 0, np.nan)
    observed = counts / totals[:, None]
    gap = (observed[0] - observed[1]) @ w
    if abs(gap) <= ROOT_TOL:
        return WeightedFit(0., 0., observed, 0, abs(gap))

    # Normalize counts jointly, preserving the relative group exposures.
    scaled = counts / totals.sum()
    groups = [(row > 0, row[row > 0], row.sum()) for row in scaled]

    def group_probability(group, slope):
        active, mass, total = group
        tilt = slope * w
        extreme = int(np.argmin(tilt))
        offsets = tilt - tilt[extreme]
        positive_offsets = offsets[active]
        if positive_offsets.min() > 0:
            boundary = np.sum(mass / positive_offsets)
            if boundary <= 1:
                p = np.zeros_like(w)
                p[active] = mass / positive_offsets
                p[extreme] = 1 - boundary
                return p

        def normalization(shift):
            if shift == 0 and positive_offsets.min() == 0:
                return np.inf
            return np.sum(mass / (shift + positive_offsets)) - 1

        # At twice the group mass, the probability sum is at most one half.
        shift = brentq(normalization, 0, 2 * total, xtol=5e-324)
        p = np.zeros_like(w)
        p[active] = mass / (shift + positive_offsets)
        return p

    def probabilities(multiplier):
        return np.stack((group_probability(groups[0], multiplier),
                         group_probability(groups[1], -multiplier)))

    def difference(multiplier):
        p = probabilities(multiplier)
        return (p[0] - p[1]) @ w

    endpoint = np.copysign(1., gap)
    try:
        for _ in range(60):
            if difference(endpoint) * gap <= 0:
                break
            endpoint *= 2
        else:
            raise RuntimeError("Could not bracket the null multiplier")
        if difference(endpoint) == 0:
            multiplier, iterations, converged = endpoint, 0, True
        else:
            multiplier, info = brentq(difference, min(0., endpoint), max(0., endpoint),
                                       xtol=ROOT_TOL, full_output=True)
            iterations, converged = info.iterations, info.converged
        null = probabilities(multiplier)
    except (ValueError, RuntimeError) as exc:
        raise RuntimeError(f"Null optimizer failed: {exc}") from exc

    null_gap = abs((null[0] - null[1]) @ w)
    if (not converged or not np.isfinite(null).all() or (null < 0).any()
            or np.max(abs(null.sum(axis=1) - 1)) > FEAS_TOL or null_gap > FEAS_TOL
            or (null[counts > 0] <= 0).any()):
        raise RuntimeError("Null optimizer returned infeasible probabilities")
    # Evaluate the likelihood difference cell by cell to avoid subtracting
    # large nearly equal log likelihoods.
    active = counts > 0
    ts = 2 * xlogy(counts[active], observed[active] / null[active]).sum()
    if not np.isfinite(ts) or ts < -TS_TOL:
        raise RuntimeError(f"Invalid likelihood ratio: {ts}")
    ts = max(0., ts)
    return WeightedFit(np.copysign(np.sqrt(ts), gap), ts, null, iterations, null_gap)

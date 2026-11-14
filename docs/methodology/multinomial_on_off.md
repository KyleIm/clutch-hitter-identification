# Weighted multinomial ON/OFF likelihood ratio

| | Binomial ON/OFF | Weighted multinomial ON/OFF |
|---|---|---|
| Outcomes | Hit and failure | Zero, unintentional walk, HBP, single, double, triple, home run |
| Weights | 0, 1 | 0, 0.70, 0.70, 0.90, 1.25, 1.60, 2.00 |
| Null | Equal hit probabilities | Equal weighted means |
| Alternative | Separate hit probabilities | Separate outcome vectors |

The eligibility and situation rules are defined in
[Appendix A.1](../analysis/appendix_a_1_weighted_on_off.md). See also the
[binomial derivation](binomial_on_off.md).

For group g, let N_g,i count outcome i, let T_g = Σ_i N_g,i, and
let p_g,i be its probability. The fixed weight is w_i, and
μ_g = Σ_i w_i p_g,i. Conditional on group totals, the model treats the
two count vectors as independently multinomial.

```text
L = ∏_g [(T_g! / ∏_i N_g,i!) ∏_i p_g,i^(N_g,i)]
ℓ = Σ_g Σ_i N_g,i log(p_g,i) + constant
p_hat_g,i = N_g,i / T_g
H0: μ_ON = μ_OFF
H1: μ_ON ≠ μ_OFF
```

The unrestricted maximum uses the empirical outcome distributions. The
null maximum uses the same objective subject to each vector summing to
one, nonnegative probabilities, and w·(p_ON − p_OFF) = 0. This last
constraint leaves room for different distributions with the same mean.

## Constrained maximum

Let s_ON = +1 and s_OFF = −1. The Lagrangian for maximizing the log
likelihood, with multipliers λ_g, η, and ν_g,i ≥ 0, is

```text
ℒ = ℓ − Σ_g λ_g (Σ_i p_g,i − 1)
      − η Σ_g s_g Σ_i w_i p_g,i + Σ_g Σ_i ν_g,i p_g,i
d_g,i = λ_g + η s_g w_i
```

For N_g,i > 0, stationarity and complementary slackness give
p_g,i = N_g,i / d_g,i > 0. For N_g,i = 0, the objective term is
identically zero. Its stationarity gives ν_g,i = d_g,i ≥ 0 and
d_g,i p_g,i = 0. Thus zero counts can receive probability only at a
zero denominator. Zero-count terms are omitted using 0 log(0) = 0.
The objective is concave and the constraints are affine, so feasible
solutions satisfying these conditions maximize the null likelihood.

For fixed η, shift the denominators by the minimum tilt η s_g w_i.
The remaining intercept is nonnegative. Solve the monotone normalization
equation on positive-count categories by Brent's method. If the intercept
can be zero and the positive-count probabilities sum to at most one,
assign the remaining mass to an unobserved category at the minimum
tilt. Tied minima have identical weights, so where that mass goes
within the ties leaves the mean and likelihood unchanged. Solve the
outer monotone equation for η to equalize the means. The penalized
group optima imply that increasing η lowers the ON-minus-OFF mean.

The solver normalizes weights to [0, 1] and divides counts by the joint
total when solving the multiplier equations. Positive affine changes
of weights preserve mean equality and the sign. The likelihood
difference uses the original counts.

```text
TS_w = 2 Σ_g Σ_i N_g,i log(p_hat_g,i / p0_g,i)
S_w = sign(μ_hat_ON − μ_hat_OFF) sqrt(TS_w)
```

## Reduction and asymptotics

With weights in {0, 1}, each mean is the probability mass in weight-1
categories. Factor the likelihood into a binomial likelihood for group
mass times conditional multinomial likelihoods within the two weight
classes. The conditional fits are the same under both hypotheses and
cancel. Removing walks and HBP then recovers the existing hit-based
statistic.

Each of the two seven-category vectors has six free parameters, for 12
in the unrestricted model. The nonconstant weights impose one independent
linear equality, giving 11 under the null. Under Wilks' theorem, with
true probabilities interior and both sample sizes growing in comparable
proportions, TS_w tends to chi-square with one degree of freedom, and
the signed root tends to standard normal. [Wilks (1938)](https://doi.org/10.1214/aoms/1177732360) Sparse counts, boundary
probabilities, and small or unbalanced samples can make those
approximations inaccurate. The simulations use independent trials.
They do not measure calibration under dependence between real batting
observations.

## Numerical checks

An empty group returns an undefined score. On the [0, 1] weight scale,
empirical gaps within 2e-14 are treated as equal. The outer multiplier
root has absolute tolerance 2e-14. The inner root uses Brent's relative
tolerance with the smallest positive float as its absolute tolerance.
Both probability sums and the null mean equality must be within 2e-9.
The solver checks nonnegativity, positive mass at every observed outcome,
convergence, and finite likelihood difference. Negative TS within 1e-8
of zero is clipped. Other failures raise an explicit error. See
[validation](../analysis/appendix_a_2_weighted_validation.md).

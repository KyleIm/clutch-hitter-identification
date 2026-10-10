# Binomial ON/OFF Likelihood-Ratio Significance

## Purpose

This note records the derivation of a binomial ON/OFF significance
statistic motivated by the likelihood-ratio construction of Li & Ma
(1983).

The original Li-Ma significance is derived for independent Poisson
counting processes. For baseball clutch analysis, however, the natural
observations are successes out of a fixed number of opportunities. The
appropriate sampling model is therefore binomial rather than Poisson.

The objective here is to retain the ON/OFF logic and likelihood-ratio
structure while replacing the Poisson likelihood with two independent
binomial likelihoods.

> **Methodological status:** This should not yet be described as a newly
> invented "Binomial Li-Ma" statistic. Mathematically, the resulting
> statistic is the likelihood-ratio test for two independent binomial
> proportions (closely related to the likelihood-ratio/G-test for a 2x2
> table). The Li-Ma connection is the ON/OFF framing and
> likelihood-ratio construction.

## 1. ON/OFF definitions

Define:

```text
N_on  = number of successes observed in the ON sample
T_on  = total number of trials in the ON sample
N_off = number of successes observed in the OFF sample
T_off = total number of trials in the OFF sample
```

Analogously to the exposure ratio in Li-Ma, define:

```text
alpha = T_on / T_off
```

For a RISP-based baseball analysis, one possible mapping is:

```text
N_on  = H_RISP
T_on  = AB_RISP
N_off = H_nonRISP
T_off = AB_nonRISP
alpha = AB_RISP / AB_nonRISP
```

Unlike the original Poisson Li-Ma problem, the absolute trial counts
`T_on` and `T_off` cannot in general be discarded. A binomial likelihood
depends on both successes and failures.

## 2. Binomial sampling model

Assume two independent binomial samples:

```text
N_on  ~ Binomial(T_on, p_on)
N_off ~ Binomial(T_off, p_off)
```

Their joint likelihood is:

```text
L(p_on, p_off)
  = choose(T_on, N_on)
    p_on^N_on
    (1 - p_on)^(T_on - N_on)
    choose(T_off, N_off)
    p_off^N_off
    (1 - p_off)^(T_off - N_off)
```

## 3. Null hypothesis

The no-ON-effect hypothesis is:

```text
H0: p_on = p_off = p
```

Under this constraint, the maximum-likelihood estimate of the common
success probability is the pooled proportion:

```text
p0_hat = (N_on + N_off) / (T_on + T_off)
```

The maximized null likelihood is therefore:

```text
L0 = L(p0_hat, p0_hat)
```

For baseball, this hypothesis means that the player's underlying success
probability is the same in clutch and non-clutch opportunities.

## 4. Alternative hypothesis

Under the unrestricted alternative:

```text
H1: p_on != p_off
```

The maximum-likelihood estimates are simply the observed proportions:

```text
p_on_hat  = N_on / T_on
p_off_hat = N_off / T_off
```

Thus:

```text
L1 = L(p_on_hat, p_off_hat)
```

## 5. Likelihood ratio

Following the likelihood-ratio logic used by Li & Ma, define:

```text
Lambda = L0 / L1
```

The likelihood-ratio test statistic is:

```text
TS_B = -2 log(Lambda)
```

The binomial coefficients are identical under the null and alternative
hypotheses and cancel in the likelihood ratio. After substitution and
simplification:

```text
TS_B = 2 [
  N_on log(p_on_hat / p0_hat)
  + (T_on - N_on) log((1 - p_on_hat) / (1 - p0_hat))
  + N_off log(p_off_hat / p0_hat)
  + (T_off - N_off) log((1 - p_off_hat) / (1 - p0_hat))
]
```

The four terms have a direct interpretation: ON successes, ON failures,
OFF successes, and OFF failures.

This is why `N_on`, `N_off`, and `alpha` alone are not sufficient for the
binomial problem. The likelihood also depends on the numbers of failures:

```text
T_on - N_on
T_off - N_off
```

## 6. Wilks theorem and significance

The alternative model contains two free probability parameters:

```text
(p_on, p_off)
```

whereas the null model contains one:

```text
p
```

The difference in dimensionality is therefore one.

Under the usual regularity conditions and for sufficiently large samples,
Wilks' theorem gives:

```text
TS_B = -2 log(Lambda) approximately follows chi-square with 1 degree
of freedom under H0.
```

Because a one-degree-of-freedom chi-square statistic corresponds
asymptotically to the square of a standard-normal statistic, a signed
significance can be defined as:

```text
S_B = sign(p_on_hat - p_off_hat) * sqrt(TS_B)
```

Hence:

```text
S_B > 0 indicates an ON excess
S_B < 0 indicates an ON deficit
```

For clutch hitting, positive values correspond to better observed
performance in the clutch sample and negative values correspond to worse
observed performance.

## 7. Relation to the Li-Ma exposure ratio

Since:

```text
alpha = T_on / T_off
```

we may write:

```text
T_on = alpha * T_off
```

Then:

```text
p_on_hat  = N_on / (alpha * T_off)
p_off_hat = N_off / T_off
p0_hat    = (N_on + N_off) / ((1 + alpha) * T_off)
```

Thus the statistic may equivalently be represented as:

```text
S_B = S_B(N_on, N_off, T_off, alpha)
```

This makes the connection with the original Li-Ma notation explicit.

The original Poisson Li-Ma significance can be written schematically as:

```text
S_LM = S(N_on, N_off, alpha)
```

whereas the binomial ON/OFF statistic requires:

```text
S_B = S(N_on, N_off, T_off, alpha)
```

or, equivalently:

```text
S_B = S(N_on, T_on, N_off, T_off)
```

The extra absolute trial-count information is required because binomial
sampling contains explicit information about both successes and failures.

## 8. Baseball specialization

For a simple hit/non-hit RISP analysis:

```text
N_on  = H_RISP
T_on  = AB_RISP
N_off = H_nonRISP
T_off = AB_nonRISP
```

The estimated success probabilities are:

```text
p_RISP_hat    = H_RISP / AB_RISP
p_nonRISP_hat = H_nonRISP / AB_nonRISP
p0_hat        = (H_RISP + H_nonRISP) / (AB_RISP + AB_nonRISP)
```

The player-level statistic is therefore:

```text
S_clutch = sign(p_RISP_hat - p_nonRISP_hat) * sqrt(TS_B)
```

This explicitly accounts for unequal RISP and non-RISP sample sizes
through the binomial likelihood.

## 9. Important caveats

### 9.1 This is not the conditional-binomial rewriting of ordinary Li-Ma

Two independent Poisson counts can be conditioned on their total count,
producing a binomial distribution for whether each event falls in the ON
or OFF region. That conditional formulation reproduces the ordinary
Li-Ma likelihood-ratio statistic.

The construction in this note is different.

Here, ON and OFF are two separate groups of Bernoulli trials, and each
group contains both successes and failures. The null hypothesis compares
their success probabilities.

### 9.2 Wilks is asymptotic

The interpretation:

```text
S_B^2 approximately follows chi-square with 1 degree of freedom
```

is asymptotic. Very small samples, extreme probabilities, or boundary
cases may require an exact test, permutation/randomization procedure, or
simulation calibration.

### 9.3 The null model may require a league-level adjustment

The simplest null is:

```text
p_on = p_off
```

If baseball context produces a systematic league-wide difference between
RISP and non-RISP performance, a later version of the model may need to
test player-specific clutch effects relative to that league-level
situational baseline rather than relative to zero difference.

### 9.4 Methodological novelty remains to be established

The resulting likelihood-ratio statistic is mathematically the standard
likelihood-ratio comparison of two binomial proportions. Any novelty
claim should therefore concern the baseball application, ON/OFF
formulation, calibration, population analysis, persistence analysis, or
other extensions, not the basic likelihood-ratio algebra unless further
methodological work establishes otherwise.

## 10. Compact formula

For implementation, define:

```text
p1 = N_on / T_on
p2 = N_off / T_off
p0 = (N_on + N_off) / (T_on + T_off)
```

Then:

```text
S_B = sign(p1 - p2) * sqrt(
  2 [
    N_on log(p1 / p0)
    + (T_on - N_on) log((1 - p1) / (1 - p0))
    + N_off log(p2 / p0)
    + (T_off - N_off) log((1 - p2) / (1 - p0))
  ]
)
```

When a count multiplying a logarithm is zero, its contribution should be
interpreted by continuity as zero:

```text
0 log(0) = 0
```

## Reference

Li, T.-P. & Ma, Y.-Q. (1983), *Analysis Methods for Results in Gamma-Ray
Astronomy*, The Astrophysical Journal, 272, 317-324.

This note uses Li & Ma as the conceptual likelihood-ratio/ON-OFF
starting point; the binomial derivation above should be cross-checked
against standard two-sample binomial likelihood-ratio and 2x2
contingency-table literature before publication.

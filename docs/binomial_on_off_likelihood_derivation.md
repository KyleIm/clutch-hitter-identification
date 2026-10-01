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

Define

$$ N_{\rm on} =
\text{number of successes observed in the ON sample}, $$

$$ T_{\rm on} =
\text{total number of trials in the ON sample}, $$

$$ N_{\rm off} =
\text{number of successes observed in the OFF sample}, $$

$$ T_{\rm off} =
\text{total number of trials in the OFF sample}. $$

Analogously to the exposure ratio in Li-Ma, define

$$ \alpha = \frac{T_{\rm on}}{T_{\rm off}}. $$

For a RISP-based baseball analysis, one possible mapping is

$$ N_{\rm on}=H_{\rm RISP}, \qquad
T_{\rm on}=AB_{\rm RISP}, $$

$$ N_{\rm off}=H_{\rm nonRISP}, \qquad
T_{\rm off}=AB_{\rm nonRISP}, $$

so that

$$ \alpha = \frac{AB_{\rm RISP}}{AB_{\rm nonRISP}}. $$

Unlike the original Poisson Li-Ma problem, the absolute trial counts
(T_{\rm on}) and (T_{\rm off}) cannot in general be
discarded. A binomial likelihood depends on both successes and failures.

## 2. Binomial sampling model

Assume two independent binomial samples:

$$
N_{\rm on}\sim {\rm Binomial}(T_{\rm on},p_{\rm on}),
$$

$$
N_{\rm off}\sim {\rm Binomial}(T_{\rm off},p_{\rm off}).
$$

Their joint likelihood is

$$ L(p_{\rm on},p_{\rm off}) =
{T_{\rm on}\choose N_{\rm on}}
p_{\rm on}^{N_{\rm on}}
(1-p_{\rm on})^{T_{\rm on}-N_{\rm on}}
{T_{\rm off}\choose N_{\rm off}}
p_{\rm off}^{N_{\rm off}}
(1-p_{\rm off})^{T_{\rm off}-N_{\rm off}}.
$$

## 3. Null hypothesis

The no-ON-effect hypothesis is

$$ H_0:\quad p_{\rm on}=p_{\rm off}=p. $$

Under this constraint, the maximum-likelihood estimate of the common
success probability is the pooled proportion

$$ \boxed{
\hat p_0 =
\frac{N_{\rm on}+N_{\rm off}}
     {T_{\rm on}+T_{\rm off}}
}. $$

The maximized null likelihood is therefore

$$ L_0=L(\hat p_0,\hat p_0). $$

For baseball, this hypothesis means that the player's underlying success
probability is the same in clutch and non-clutch opportunities.

## 4. Alternative hypothesis

Under the unrestricted alternative,

$$
H_1:\quad p_{\rm on}\neq p_{\rm off}.
$$

The maximum-likelihood estimates are simply the observed proportions:

$$ \boxed{
\hat p_{\rm on}=\frac{N_{\rm on}}{T_{\rm on}}
}, $$

$$ \boxed{
\hat p_{\rm off}=\frac{N_{\rm off}}{T_{\rm off}}
}. $$

Thus

$$
L_1=L(\hat p_{\rm on},\hat p_{\rm off}).
$$

## 5. Likelihood ratio

Following the likelihood-ratio logic used by Li & Ma, define

$$ \Lambda=\frac{L_0}{L_1}. $$

The likelihood-ratio test statistic is

$$ TS_B=-2\ln\Lambda. $$

The binomial coefficients are identical under the null and alternative
hypotheses and cancel in the likelihood ratio. After substitution and
simplification,

$$ \boxed{
\begin{aligned}
TS_B=2\Bigg[
&N_{\rm on}\ln\left(\frac{\hat p_{\rm on}}{\hat p_0}\right)
+(T_{\rm on}-N_{\rm on})
 \ln\left(\frac{1-\hat p_{\rm on}}{1-\hat p_0}\right)\\
&+N_{\rm off}\ln\left(\frac{\hat p_{\rm off}}{\hat p_0}\right)
+(T_{\rm off}-N_{\rm off})
 \ln\left(\frac{1-\hat p_{\rm off}}{1-\hat p_0}\right)
\Bigg].
\end{aligned}
} $$

The four terms have a direct interpretation: ON successes, ON failures,
OFF successes, and OFF failures.

This is why (N_{\rm on}), (N_{\rm off}), and
(\alpha) alone are not sufficient for the binomial problem. The
likelihood also depends on the numbers of failures,

$$ T_{\rm on}-N_{\rm on}
\quad\text{and}\quad
T_{\rm off}-N_{\rm off}. $$

## 6. Wilks theorem and significance

The alternative model contains two free probability parameters,

$$ (p_{\rm on},p_{\rm off}), $$

whereas the null model contains one,

$$ p. $$

The difference in dimensionality is therefore one.

Under the usual regularity conditions and for sufficiently large
samples, Wilks' theorem gives

$$ TS_B=-2\ln\Lambda
\overset{H_0}{\approx}\chi^2_1. $$

Because a one-degree-of-freedom chi-square statistic corresponds
asymptotically to the square of a standard-normal statistic, a signed
significance can be defined as

$$ \boxed{
S_B =
{\rm sgn}(\hat p_{\rm on}-\hat p_{\rm off})
\sqrt{TS_B}
}. $$

Hence

$$ S_B>0 $$

indicates an ON excess, while

$$ S_B<0 $$

indicates an ON deficit.

For clutch hitting, positive values correspond to better observed
performance in the clutch sample and negative values correspond to worse
observed performance.

## 7. Relation to the Li-Ma exposure ratio

Since

$$ \alpha=\frac{T_{\rm on}}{T_{\rm off}}, $$

we may write

$$ T_{\rm on}=\alpha T_{\rm off}. $$

Then

$$ \hat p_{\rm on} =
\frac{N_{\rm on}}{\alpha T_{\rm off}}, $$

$$ \hat p_{\rm off} =
\frac{N_{\rm off}}{T_{\rm off}}, $$

and

$$ \hat p_0 = \frac{N_{\rm on}+N_{\rm off}}
{(1+\alpha)T_{\rm off}}. $$

Thus the statistic may equivalently be represented as

$$ S_B =
S_B(N_{\rm on},N_{\rm off},T_{\rm off},\alpha).
$$

This makes the connection with the original Li-Ma notation explicit.

The original Poisson Li-Ma significance can be written schematically as

$$
S_{\rm LM}=S(N_{\rm on},N_{\rm off},\alpha),
$$

whereas the binomial ON/OFF statistic requires

$$
S_B=S(N_{\rm on},N_{\rm off},T_{\rm off},\alpha),
$$

or, equivalently,

$$
S_B=S(N_{\rm on},T_{\rm on},N_{\rm off},T_{\rm off}).
$$

The extra absolute trial-count information is required because binomial
sampling contains explicit information about both successes and
failures.

## 8. Baseball specialization

For a simple hit/non-hit RISP analysis,

$$ N_{\rm on}=H_{\rm RISP}, \qquad
T_{\rm on}=AB_{\rm RISP}, $$

$$ N_{\rm off}=H_{\rm nonRISP}, \qquad
T_{\rm off}=AB_{\rm nonRISP}. $$

The estimated success probabilities are

$$ \hat p_{\rm RISP} =
\frac{H_{\rm RISP}}{AB_{\rm RISP}}, $$

$$ \hat p_{\rm nonRISP} =
\frac{H_{\rm nonRISP}}{AB_{\rm nonRISP}}, $$

with pooled null estimate

$$ \hat p_0 = \frac{H_{\rm RISP}+H_{\rm nonRISP}}
{AB_{\rm RISP}+AB_{\rm nonRISP}}. $$

The player-level statistic is therefore

$$ \boxed{
S_{\rm clutch}
=
{\rm sgn}
(\hat p_{\rm RISP}-\hat p_{\rm nonRISP})
\sqrt{TS_B}
}. $$

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

The interpretation

$$ S_B^2\approx\chi^2_1 $$

is asymptotic. Very small samples, extreme probabilities, or boundary
cases may require an exact test, permutation/randomization procedure, or
simulation calibration.

### 9.3 The null model may require a league-level adjustment

The simplest null is

$$ p_{\rm on}=p_{\rm off}. $$

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

For implementation, define

$$ p_1=\frac{N_{\rm on}}{T_{\rm on}}, \qquad
p_2=\frac{N_{\rm off}}{T_{\rm off}}, \qquad
p_0=\frac{N_{\rm on}+N_{\rm off}}
{T_{\rm on}+T_{\rm off}}. $$

Then

$$ \boxed{
\begin{aligned}
S_B
=&\ {\rm sgn}(p_1-p_2)
\Bigg\{
2\Big[
N_{\rm on}\ln(p_1/p_0)
+(T_{\rm on}-N_{\rm on})
 \ln((1-p_1)/(1-p_0))\\
&\qquad\qquad
+N_{\rm off}\ln(p_2/p_0)
+(T_{\rm off}-N_{\rm off})
 \ln((1-p_2)/(1-p_0))
\Big]
\Bigg\}^{1/2}.
\end{aligned}
} $$

When a count multiplying a logarithm is zero, its contribution should be
interpreted by continuity as zero:

$$
0 \ln 0 = 0.
$$

## Reference

Li, T.-P. & Ma, Y.-Q. (1983), *Analysis Methods for Results in Gamma-Ray
Astronomy*, The Astrophysical Journal, 272, 317-324.

This note uses Li & Ma as the conceptual likelihood-ratio/ON-OFF
starting point; the binomial derivation above should be cross-checked
against standard two-sample binomial likelihood-ratio and 2x2
contingency-table literature before publication.

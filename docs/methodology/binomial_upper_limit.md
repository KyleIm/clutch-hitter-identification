# Zech-inspired Bayesian binomial upper limit

[See the consolidated derivation in Appendix C](../analysis/appendix_c_mathematical_derivations.md#c4--bayesian-upper-limits-for-binomial-onoff).

Li–Ma motivates the signed likelihood-ratio detection statistic used
in the [binomial ON/OFF framework](binomial_on_off.md). For upper limits,
we use the normalization over nonnegative signal strengths in the
Bayesian Poisson formula discussed in Zech (1989, Eq. 1) as motivation.
Zech also gave a classical interpretation for that Poisson formula.
The baseball calculation instead conditions a Bayesian posterior over a
difference of binomial probabilities. Kawasaki and Miyaoka (2010,
Theorem 1) derive the density of that difference and use it for
highest-posterior-density intervals. Here we use the difference
distribution to compute a one-sided conditional quantile.

- G. Zech (1989), *Upper limits in experiments with background or measurement errors*, Nuclear Instruments and Methods in Physics Research A **277**(2–3), 608–610. [DOI](https://doi.org/10.1016/0168-9002%2889%2990795-X) · [CERN preprint](https://cds.cern.ch/record/193135/files/198812358.pdf).
- Youhei Kawasaki and Etsuo Miyaoka (2010), *A Posterior Density for the Difference Between Two Binominal Proportions and the Highest Posterior Density Credible Interval*, Journal of the Japan Statistical Society **40**(2), 265–275. [DOI](https://doi.org/10.14490/jjss.40.265) · [Full text](https://www.jstage.jst.go.jp/article/jjss/40/2/40_2_265/_pdf).

## Posterior for the ON-minus-OFF effect

For each side `j` in ON and OFF, the independent likelihood is
$N_j\sim\mathrm{Bin}(T_j,p_j)$, where $N_j$ is hits and $T_j$ is eligible
trials. Independent uniform priors $p_j\sim\mathrm{Beta}(1,1)$ give
posterior kernels $p_j^{N_j}(1-p_j)^{T_j-N_j}$ and hence independent
posteriors $p_j\mid D\sim\mathrm{Beta}(N_j+1,T_j-N_j+1)$.

Let $\delta=p_{\mathrm{on}}-p_{\mathrm{off}}$. Change variables from
$(p_{\mathrm{on}},p_{\mathrm{off}})$ to $(x,p)=(\delta,p_{\mathrm{off}})$.
The Jacobian has absolute determinant 1. Both probabilities must lie
in $[0,1]$, giving the density on $[-1,1]$

```math
f_\delta(x\mid D)=\int_{\max(0,-x)}^{\min(1,1-x)}
f_{\mathrm{on}}(p+x)f_{\mathrm{off}}(p)\,dp.
```

We condition on $\delta\ge0$ to answer how large a positive effect
could be. Negative effects remain possible in baseball. The 95% limit
solves

```math
\boxed{
\frac{\int_0^{\delta_{\mathrm{UL}}} f_\delta(x\mid D)\,dx}
{\int_0^1 f_\delta(x\mid D)\,dx}
= P(\delta\le\delta_{\mathrm{UL}}\mid D,\delta\ge0)=0.95.
}
```

The prior is uniform separately in the rates, which induces a
triangular prior for their difference. The posterior positive
probability $P(\delta>0\mid D)$ is reported separately. A tight limit
can accompany a very small positive probability. The credibility
statement applies to this conditional posterior and carries no guarantee
of 95% frequentist coverage.

## One-dimensional calculation

For $0\le d\le1$, conditional on $p_{\mathrm{off}}=p$, the event
$\delta>d$ requires $p_{\mathrm{on}}>p+d$ and is possible only when
$p<1-d$. Averaging over the OFF posterior gives

```math
Q(d)=P(\delta>d\mid D)=\int_0^{1-d} f_{\mathrm{off}}(p)
[1-F_{\mathrm{on}}(p+d)]\,dp.
```

Since the posterior is continuous, the conditional CDF at $d$ is
$1-Q(d)/Q(0)$. Solve $Q(\delta_{\mathrm{UL}})=0.05Q(0)$ for the
95% limit, or replace 0.05 by one minus the requested level.

The implementation uses Beta survival probabilities directly and an
exact log-space binomial sum when the survival is too small for
reliable ordinary arithmetic. For integer $a,b$, the Beta survival at
$p$ equals the lower tail of a binomial with $a+b-1$ trials and
success probability $p$, through $a-1$ successes. Scaling the
integrand at its mode and placing quadrature breakpoints around the
peak resolves narrow tails. Brent's method solves the log-tail ratio.
The returned log positive probability remains informative after
floating-point underflow of the probability itself. Integration error,
evaluation count, root iterations and attained conditional mass are
recorded. Convergence errors raise exceptions. Zero trials on either
side make the observed comparison undefined and are explicitly
excluded. Zero-hit and all-hit groups retain proper Beta posteriors.

[Player analysis and numerical validation](../analysis/02_upper_limit_analysis.md)

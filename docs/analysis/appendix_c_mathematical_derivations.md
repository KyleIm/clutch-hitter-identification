# Appendix C — Mathematical Derivations

The first three sections develop the signed ON/OFF detection statistic and the overlap-aware test. C.4 derives the upper limit used in Step 2. C.5 and C.6 develop the weighted extension used in Appendix A.

- [C.1 — From Poisson to binomial ON/OFF statistics](#c1--from-poisson-to-binomial-onoff-statistics)
- [C.2 — Derivation of the binomial ON/OFF statistic](#c2--derivation-of-the-binomial-onoff-statistic)
- [C.3 — Asymptotic distribution and statistical interpretation](#c3--asymptotic-distribution-and-statistical-interpretation)
- [C.4 — Bayesian upper limits for binomial ON/OFF](#c4--bayesian-upper-limits-for-binomial-onoff)
- [C.5 — Weighted multinomial ON/OFF framework](#c5--weighted-multinomial-onoff-framework)
- [C.6 — Reduction to the binomial statistic](#c6--reduction-to-the-binomial-statistic)

## C.1 — From Poisson to binomial ON/OFF statistics

In the astronomical ON/OFF setup, let $x,y$ be the observed counts in a signal region and a background control region, respectively. Let $\alpha>0$ be the known ratio of ON to OFF effective exposure. If $b$ is the expected OFF background and $s$ the expected ON excess, the independent counts have means $\mu_{\mathrm{on}}=s+\alpha b$ and $\mu_{\mathrm{off}}=b$. The joint likelihood is

```math
L(s,b)=\frac{(s+\alpha b)^x e^{-(s+\alpha b)}}{x!}
       \frac{b^y e^{-b}}{y!}.
```

The null is $s=0$. For the two-sided signed comparison, the alternative allows separate nonnegative ON and OFF means, so $s$ can describe an excess or a deficit. A signal-only alternative with $s\geq0$ would put the optimum at the null boundary when $x<\alpha y$. Maximizing the two separate Poisson terms gives $\widehat\mu_{\mathrm{on}}=x$ and $\widehat\mu_{\mathrm{off}}=y$, with boundary maxima at zero for zero counts. Under the null, up to count-dependent constants,

```math
\ell_0(b)=x\log\alpha+(x+y)\log b-(1+\alpha)b,\qquad
\frac{d\ell_0}{db}=\frac{x+y}{b}-(1+\alpha).
```

Thus $\widehat b_0=(x+y)/(1+\alpha)$ and the fitted ON background is $\alpha\widehat b_0$. The two fitted means sum to $x+y$ under either fit, so the linear terms cancel when taking the log likelihood ratio. Substitution yields the squared Li–Ma statistic,

```math
G_{\mathrm P}
=2\left[
x\log\!\left(\frac{1+\alpha}{\alpha}\frac{x}{x+y}\right)
+y\log\!\left((1+\alpha)\frac{y}{x+y}\right)
\right].
```

A zero count contributes zero by continuity, and the all-zero case has equal maximized likelihoods. The score takes the sign of $x-\alpha y$ times the square root. [Li and Ma (1983), *The Astrophysical Journal* 272, 317–324, Eq. 17](https://articles.adsabs.harvard.edu/pdf/1983ApJ...272..317L)

Batting supplies a known number $T_j$ of eligible trials per group, with one hit-or-failure outcome per trial. Conditional on $T_j$, the binomial variance is $T_jp_j(1-p_j)$, while a Poisson approximation at the same mean has variance $T_jp_j$ and ignores the upper bound on successes. When $p_j$ is appreciable, the variance difference matters. The baseball statistic carries over the ON/OFF comparison and signed root, using a binomial sampling model conditional on trial totals. Conditioning the *Poisson* model on $x+y$ would instead give a binomial for the allocation of those events between regions, a different experiment. [Original binomial methodology](../methodology/binomial_on_off.md)

## C.2 — Derivation of the binomial ON/OFF statistic

For $j\in\{\mathrm{on},\mathrm{off}\}$ let $T_j>0$ count eligible trials, $H_j$ count hits, and $F_j=T_j-H_j$ count failures. Under independent trials within each group and independent groups for this particular split, the conditional likelihood is

```math
L(p_{\mathrm{on}},p_{\mathrm{off}})
=\prod_j {T_j\choose H_j} p_j^{H_j}(1-p_j)^{F_j}.
```

The null $H_0$ sets $p_{\mathrm{on}}=p_{\mathrm{off}}=p$. The unrestricted fit used for the alternative allows two separate rates. Discarding the common combinatorial constant, each log likelihood contribution and its derivative are

```math
\ell_j(p_j)=H_j\log p_j+F_j\log(1-p_j),\qquad
\ell_j'(p_j)=\frac{H_j-T_jp_j}{p_j(1-p_j)}.
```

The derivative changes from positive to negative at $\widehat p_j=H_j/T_j$ for interior samples. When all outcomes in a group agree, the same estimator gives the boundary maximum. Under $H_0$, summing the derivatives at the common rate gives

```math
\ell_0'(p)=
\frac{H_{\mathrm{on}}+H_{\mathrm{off}}-(T_{\mathrm{on}}+T_{\mathrm{off}})p}{p(1-p)},
\qquad
\widehat p_0=\frac{H_{\mathrm{on}}+H_{\mathrm{off}}}{T_{\mathrm{on}}+T_{\mathrm{off}}}.
```

The likelihood ratio $\Lambda$ is the restricted maximum divided by the unrestricted maximum. The binomial coefficients cancel. Explicitly, the ratio is the product over groups of the hit-probability ratio raised to the hit count and the failure-probability ratio raised to the failure count.

```math
\Lambda=\prod_j\left(\frac{\widehat p_0}{\widehat p_j}\right)^{H_j}
\left(\frac{1-\widehat p_0}{1-\widehat p_j}\right)^{F_j}.
```

Taking $-2\log\Lambda$ converts these products to sums and gives

```math
G=2\sum_j\left[
H_j\log\frac{H_j}{T_j\widehat p_0}
+F_j\log\frac{F_j}{T_j(1-\widehat p_0)}
\right],
\qquad
S=\mathrm{sgn}(\widehat p_{\mathrm{on}}-\widehat p_{\mathrm{off}})\sqrt G.
```

The expected counts are each row total times the corresponding pooled column proportion. This is exactly the likelihood-ratio $G$ statistic for the $2\times2$ table of group by outcome. A zero observed count contributes zero. If both groups have only hits or only failures, the unrestricted and pooled fits agree and the score is zero. A boundary fit for one nonempty group remains valid by the same zero-count convention. An empty group has undefined rate and score. The implementation computes direction using the cross-product of counts and truncates negative roundoff in $G$ at zero. [Binomial score implementation](../../Script/lima_histogram_RISP_sample.py) · [Eligibility and baseline](00_baseline_analysis.md)

## C.3 — Asymptotic distribution and statistical interpretation

The unrestricted binomial model has two free rates and the null has one. With a true common rate strictly inside $(0,1)$ and both sample sizes growing with a nonvanishing share of total trials, the two models are smooth around the truth. Wilks' theorem then gives $G\to\chi^2_1$ in distribution. To see the sign interpretation, let $\Delta=\widehat p_{\mathrm{on}}-\widehat p_{\mathrm{off}}$. A second-order likelihood expansion around the pooled fit gives

```math
G=\frac{\Delta^2}{\widehat p_0(1-\widehat p_0)(1/T_{\mathrm{on}}+1/T_{\mathrm{off}})}
  +o_p(1).
```

Indeed, each group contributes $T_j(\widehat p_j-\widehat p_0)^2/[\widehat p_0(1-\widehat p_0)]$ to second order. The pooled rate is the trial-weighted average, so the two terms combine into the displayed expression. The binomial central limit theorem gives an asymptotically normal standardized $\Delta$ under the null, and the signed root has the same limit $N(0,1)$. Sparse cells, near-boundary rates, or a group with few observations can compromise this calibration. $S$ measures evidence and depends on the sample sizes. $\Delta$ measures the observed effect on the hit-rate scale. Neither establishes a persistent player ability from pooled observations. [Wilks (1938)](https://doi.org/10.1214/aoms/1177732360)

### Overlap between RISP and LIPS

For one hitter, partition eligible trials into four disjoint cells $c\in\{00,10,01,11\}$, where the first digit marks RISP and the second marks LIPS. Their trial and hit totals are $T_c$ and $H_c$. RISP ON sums $10,11$ and OFF sums $00,01$. LIPS ON sums $01,11$ and OFF sums $00,10$.

For either situation $J$, write its raw ON-minus-OFF contrast as $\Delta_J=\sum_c a_{Jc}H_c$, where $a_{Jc}=1/T_{J,\mathrm{on}}$ if $c$ belongs to ON and $a_{Jc}=-1/T_{J,\mathrm{off}}$ otherwise. Under the Step 1 working null of a common fixed $p$ for the hitter and independent counts in the disjoint cells conditional on their trial totals, bilinearity and $\mathrm{Var}(H_c)=T_cp(1-p)$ give

```math
\mathrm{Cov}(\Delta_{\mathrm{RISP}},\Delta_{\mathrm{LIPS}}\mid T,p)
=p(1-p)\sum_c T_c a_{\mathrm{RISP},c}a_{\mathrm{LIPS},c}.
```

The neither and both cells give positive contributions, and the single-situation cells give negative contributions. This is a within-player covariance for raw contrasts under the specified model. The analysis uses simulation to propagate dependence through the nonlinear scores and the across-player correlation.

Estimate one pooled rate per hitter, $\widehat p=\sum_c H_c/\sum_c T_c$. In each replicate independently draw $H_c^*\sim\mathrm{Bin}(T_c,\widehat p)$ across disjoint cells for that hitter. Reconstruct both score vectors from the same simulated counts, then compute Pearson and Spearman correlations on each existing PA sample. The one-sided Monte Carlo tail is $(1+\#\{r^*\ge r_{\mathrm{obs}}\})/(1+B)$ for $B$ replicates. This is a plug-in null simulation with fixed trial totals and estimated hitter rates. [Step 1 analysis](01_risp_lips_correlation.md#statistical-hypothesis-testing) · [Simulation implementation](../../Script/analyze_risp_lips.py)

## C.4 — Bayesian upper limits for binomial ON/OFF

For a Poisson count $n$ with known mean background $b$, the Bayesian expression discussed by Zech normalizes the likelihood over nonnegative signal strength $s$. With a flat prior over that region, the posterior probability above an upper limit $U$ is

```math
\frac{\int_U^\infty \Pr(n\mid b+s)\,ds}
     {\int_0^\infty \Pr(n\mid b+s)\,ds}.
```

The baseball limit borrows the normalization idea. A negative batting effect remains possible, and conditioning on a positive effect specifies the question being answered. Kawasaki and Miyaoka provide the difference-of-proportions framework. Their highest-posterior-density intervals address a different posterior summary from this conditional quantile. [Zech (1989), Eq. 1](https://doi.org/10.1016/0168-9002%2889%2990795-X) · [Kawasaki and Miyaoka (2010)](https://doi.org/10.14490/jjss.40.265)

Assign independent $\mathrm{Beta}(1,1)$ priors to the two rates. Multiplying each constant prior density by its binomial likelihood leaves the kernel $p_j^{H_j}(1-p_j)^{F_j}$. Integrating that kernel gives $B(H_j+1,F_j+1)$, where $B$ is the beta function. Hence the normalized posterior factors into two independent beta densities,

```math
f_j(p_j\mid D)
=\frac{p_j^{H_j}(1-p_j)^{F_j}}{B(H_j+1,F_j+1)},
\qquad
p_j\mid D\sim\mathrm{Beta}(H_j+1,F_j+1).
```

Set $\delta=p_{\mathrm{on}}-p_{\mathrm{off}}$ and $q=p_{\mathrm{off}}$. The inverse map is $(p_{\mathrm{on}},p_{\mathrm{off}})=(q+\delta,q)$ with Jacobian determinant one. For a given $\delta=d$, the unit-square constraints give $q\ge0$, $q\ge-d$, $q\le1$, and $q\le1-d$. Thus

```math
f_\delta(d\mid D)=
\int_{\max(0,-d)}^{\min(1,1-d)}
f_{\mathrm{on}}(q+d\mid D) f_{\mathrm{off}}(q\mid D)\,dq,
\qquad -1\le d\le1.
```

The density is zero outside that interval. Independent uniform priors on the rates yield prior density $1-|d|$ on $[-1,1]$, because the integration interval then has that length and the joint prior density is one.

The positive probability is $\pi_+=\int_0^1 f_\delta(d\mid D)\,dd$. Continuity means that $\delta=0$ has no point mass. On $[0,1]$, the conditional density is $f_\delta(d\mid D)/\pi_+$. The limit $U$ therefore solves

```math
\frac{\int_0^U f_\delta(d\mid D)\,dd}{\pi_+}
=\Pr(\delta\le U\mid D,\delta\ge0)=0.95.
```

For efficient evaluation, condition first on $q=p_{\mathrm{off}}$. For $d\ge0$, the event $\delta>d$ requires $p_{\mathrm{on}}>q+d$ and $q<1-d$. Integrating over the OFF posterior gives the survival function

```math
Q(d)=\Pr(\delta>d\mid D)
=\int_0^{1-d} f_{\mathrm{off}}(q\mid D)
\left[1-F_{\mathrm{on}}(q+d\mid D)\right]\,dq.
```

Since $\pi_+=Q(0)$, the conditional CDF is $1-Q(d)/Q(0)$ and the root satisfies $Q(U)=0.05Q(0)$. The implementation evaluates the beta survival function directly. For integer posterior shapes $a,b$ the survival at $z$ equals $\sum_{k=0}^{a-1}{a+b-1\choose k}z^k(1-z)^{a+b-1-k}$, evaluated by log-sum-exp when the ordinary survival becomes extremely small. It locates the log-integrand peak, scales the integrand by its peak value, and places quadrature breakpoints around that peak. The solver applies Brent's method to $\log Q(d)-\log Q(0)-\log(0.05)$ and checks the attained conditional mass. $\log Q(0)$ remains useful when the reported probability underflows. Zero-hit and all-hit samples have proper posteriors. The implementation excludes players with an empty ON or OFF sample.

A small $U$ describes the positive portion of the posterior and can coexist with a very small $\pi_+$. The credible limit is conditional on the sign and carries no unconditional frequentist coverage guarantee. [Upper-limit methodology](../methodology/binomial_upper_limit.md) · [Implementation](../../Script/binomial_upper_limit.py) · [Step 2 results](02_upper_limit_analysis.md)

## C.5 — Weighted multinomial ON/OFF framework

For group $j$ and outcome $i$, let $N_{ji}$ be the count, $T_j=\sum_i N_{ji}$, and $p_{ji}$ the probability. Fix weights $w_i$ and write expected batting production as $\mu_j=\sum_i w_i p_{ji}$. Given their totals the two groups have independent multinomial likelihoods,

```math
L=\prod_j\left[\frac{T_j!}{\prod_i N_{ji}!}\prod_i p_{ji}^{N_{ji}}\right],
\qquad
\ell=\sum_{j,i} N_{ji}\log p_{ji}+\mathrm{constant}.
```

Each probability vector lies in the simplex, with $p_{ji}\ge0$ and $\sum_i p_{ji}=1$. Maximizing each group separately gives $\widehat p_{ji}=N_{ji}/T_j$. In particular, for positive-count cells, stationarity with multiplier $\lambda_j$ gives $N_{ji}/p_{ji}=\lambda_j$, and normalization yields $\lambda_j=T_j$. A zero-count cell receives zero mass in this fit because increasing the mass available to observed outcomes increases the likelihood.

Under $H_0$ impose $\mu_{\mathrm{on}}=\mu_{\mathrm{off}}$, which permits different probability vectors with the same weighted mean. Let $s_{\mathrm{on}}=1$, $s_{\mathrm{off}}=-1$. Introduce multipliers $\lambda_j$ for normalization, $\eta$ for mean equality, and $\nu_{ji}\ge0$ for nonnegativity. The Lagrangian is

```math
\mathcal L=\ell-\sum_j\lambda_j\Big(\sum_i p_{ji}-1\Big)
-\eta\sum_{j,i}s_j w_i p_{ji}
+\sum_{j,i}\nu_{ji}p_{ji}.
```

Writing $d_{ji}=\lambda_j+\eta s_j w_i$, the KKT conditions combine feasibility, stationarity, and $\nu_{ji}p_{ji}=0$. A positive count requires positive mass for finite likelihood, so $\nu_{ji}=0$ and

```math
N_{ji}>0\quad\Longrightarrow\quad
N_{ji}/p_{ji}=d_{ji},\qquad p_{ji}=N_{ji}/d_{ji}>0.
```

A zero-count cell contributes a constant zero. Its stationarity becomes $\nu_{ji}=d_{ji}\ge0$, with $d_{ji}p_{ji}=0$. Thus an unobserved outcome can have positive mass under the null when its denominator is zero. Concavity of the log likelihood and affine feasibility make these conditions sufficient for a global maximum.

For fixed $\eta$ and group $j$, let $m_j=\min_i(\eta s_j w_i)$, $u_j=\lambda_j+m_j$, and $v_{ji}=\eta s_j w_i-m_j\ge0$. Solve the decreasing normalization equation $\sum_{i:N_{ji}>0}N_{ji}/(u_j+v_{ji})=1$ with Brent's method when $u_j>0$. If the sum at $u_j=0$ is finite and at most one, assign the leftover probability to an unobserved minimum-tilt cell. Ties have equal tilt and, for nonzero $\eta$, equal weight. The remaining outer constraint is $\sum_{j,i}s_jw_i p_{ji}(\eta)=0$. The fitted difference is nonincreasing in $\eta$: comparing the optima of $\ell-\eta(\mu_{\mathrm{on}}-\mu_{\mathrm{off}})$ at $\eta_1<\eta_2$ and adding their optimality inequalities gives $(\eta_2-\eta_1)(\Delta_\mu(\eta_1)-\Delta_\mu(\eta_2))\ge0$. The code brackets the outer root and uses Brent's method here as well. The coupled normalization and mean constraints for multiple distinct weights generally require numerical optimization.

The solver rescales the weights to $[0,1]$ and divides the counts by the joint total for the multiplier calculations. It checks feasibility and convergence, and uses original counts when computing the statistic. An empty group has undefined score. With $\widetilde p$ the constrained fit and $\widehat\mu_j=\sum_i w_i\widehat p_{ji}$, the likelihood ratio and signed root are

```math
G_w=2\sum_{j,i:N_{ji}>0}N_{ji}\log\frac{\widehat p_{ji}}{\widetilde p_{ji}},
\qquad
S_w=\mathrm{sgn}(\widehat\mu_{\mathrm{on}}-\widehat\mu_{\mathrm{off}})\sqrt{G_w}.
```

With $K$ outcomes there are $2(K-1)$ free coordinates in the unrestricted model. One independent mean constraint for nonconstant weights leaves $2(K-1)-1$ under the null (12 and 11 for seven outcomes). With interior true probabilities and both samples growing in comparable proportions, Wilks' theorem gives a $\chi^2_1$ limit for $G_w$. The contrast is smooth and has nonzero asymptotic variance under those conditions, so its signed likelihood root tends to $N(0,1)$. Boundary or sparse cases can depart from these approximations. [Weighted methodology and numerical tolerances](../methodology/multinomial_on_off.md) · [Implementation](../../Script/multinomial_on_off.py)

## C.6 — Reduction to the binomial statistic

Let $I_1$ and $I_0$ be the weight-one and weight-zero categories. Define $q_j=\sum_{i\in I_1}p_{ji}$, $H_j=\sum_{i\in I_1}N_{ji}$, and $F_j=\sum_{i\in I_0}N_{ji}$. Factor probabilities as $p_{ji}=q_j r_{j1i}$ for $i\in I_1$ and $p_{ji}=(1-q_j)r_{j0i}$ for $i\in I_0$, where the $r_{jki}$ are conditional probabilities within each class. The group likelihood factors as

```math
L_j
={T_j\choose H_j}q_j^{H_j}(1-q_j)^{F_j}
\frac{H_j!}{\prod_{i\in I_1}N_{ji}!}\prod_{i\in I_1}r_{j1i}^{N_{ji}}
\frac{F_j!}{\prod_{i\in I_0}N_{ji}!}\prod_{i\in I_0}r_{j0i}^{N_{ji}}.
```

The mean is $q_j$, so the null restricts only the two class masses to agree. The conditional multinomial factors maximize at the same within-class empirical proportions in both fits. A class with zero observed count contributes one regardless of its conditional probabilities. These factors therefore cancel in the ratio, leaving the likelihood ratio of the two aggregated binomials. The sign is the same because the empirical weighted mean is $H_j/T_j$. Recovery of the project's binomial score requires the same eligible trials, including exclusion of walks and hit-by-pitches. Assigning those outcomes weight zero while retaining them would instead change the trial counts.

For transformed weights $w_i'=a+bw_i$ with $b>0$, every fitted mean becomes $a+b\mu_j$, because each probability vector sums to one. Equality of means defines the same feasible null set and the sign of the empirical gap is preserved. Both optimized likelihoods and the signed statistic are consequently invariant. The existing validation reproduces all defined binomial scores in both situations within its declared tolerance. [Numerical reduction and affine-invariance checks](appendix_a_2_weighted_validation.md#numerical-consistency) · [Recorded validation results](../../Results/Weighted_ON_OFF/Validation/binomial_reduction.csv)

[Back to analysis navigation](../../README.md#analysis-navigation)

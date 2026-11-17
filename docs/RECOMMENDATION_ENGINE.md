# Adaptive Recommendation Engine Specification

**Project Title:** AdaptivePrep: An Explainable, Performance-Driven Adaptive Learning Platform for Personalized Placement Preparation  
**Institution:** Medi-Caps University, Indore  
**Document:** `/docs/RECOMMENDATION_ENGINE.md`  
**Current Algorithm Version:** `v1.0.0`  
**Date:** November 17, 2026  

---

## 1. Overview & Pedagogical Objective

AdaptivePrep departs from conventional static question banks (which present fixed, linear, or uniformly random questions) by continuously estimating a learner's domain-specific proficiency and serving placement-tailored questions at the frontier of their competence.

The recommendation engine is governed by three primary engineering criteria:
1. **Explainability:** Every question selection is supported by human-interpretable rationale grounded in actual performance metrics. No black-box neural networks or uncalibrated language model hallucinations.
2. **Deterministic Reproducibility:** Given identical historical attempt sequences, the engine produces mathematically deterministic proficiency scores and candidate selections.
3. **Multi-Factor Sensitivity:** Recommendations account for historical accuracy, recent trajectory, problem difficulty, and solving efficiency.

---

## 2. Mathematical Formulation

The topic proficiency score $S \in [0.0, 100.0]$ is computed as:

$$S = 100 \times \left( w_A \cdot A + w_R \cdot R + w_D \cdot D + w_E \cdot E \right)$$

Where the standard baseline weights are configured as:
- $w_A = 0.45$: Historical accuracy weight
- $w_R = 0.25$: Recent trajectory weight
- $w_D = 0.20$: Question difficulty weight
- $w_E = 0.10$: Solving efficiency weight

$$\sum w_i = 0.45 + 0.25 + 0.20 + 0.10 = 1.00$$

---

## 3. Component Normalization & Calculations

### 3.1 Historical Accuracy ($A \in [0.0, 1.0]$)
To prevent extreme volatility on the first few attempts (e.g., scoring 100% on a single lucky attempt or 0% on a single careless mistake), Laplace smoothing ($\alpha=1, \beta=1$) is applied over all topic attempts:

$$A = \frac{k + 1.0}{n + 2.0}$$

Where:
- $k$: Number of correct attempts in the topic.
- $n$: Total attempts recorded in the topic.
- **Cold Start:** If $n = 0$, $A = \frac{0 + 1}{0 + 2} = 0.50$ (unbiased diagnostic prior).

### 3.2 Recent Performance ($R \in [0.0, 1.0]$)
Measures the student's recent performance trajectory over the last $W$ attempts (default window $W = 5$) using a linear ramp weighting scheme where newer attempts carry proportionally greater weight:

$$R = \frac{\sum_{i=1}^{m} i \cdot \mathbb{I}(\text{attempt}_i \text{ is correct})}{\sum_{i=1}^{m} i}$$

Where $m = \min(n, W)$, and attempts are ordered chronologically.
- If $n = 0$, $R = 0.50$.
- **Pedagogical Effect:** A student who previously struggled but has answered the last 3 questions correctly exhibits $R > A$, enabling faster progression out of easier tiers.

### 3.3 Difficulty Performance ($D \in [0.0, 1.0]$)
Evaluates capability across problem complexity tiers:
- $\text{weight}(\text{Easy}) = 0.40$
- $\text{weight}(\text{Medium}) = 0.70$
- $\text{weight}(\text{Hard}) = 1.00$

$$D = \frac{\sum_{i=1}^{n} \text{weight}(\text{difficulty}_i) \cdot \mathbb{I}(\text{attempt}_i \text{ is correct})}{\sum_{i=1}^{n} \text{weight}(\text{difficulty}_i)}$$

Where:
- If $n = 0$, $D = 0.50$.
- **Anti-Exploit Safeguard:** Merely attempting Hard questions does not inflate $D$; credit is only earned for correct solutions. Solving a Hard question yields $2.5\times$ more earned weight than an Easy question.

### 3.4 Solving Efficiency ($E \in [0.0, 1.0]$)
Measures solving duration $t_{\text{actual}}$ relative to expected duration $t_{\text{expected}}$ (typically 60s - 120s):

$$\rho = \frac{t_{\text{actual}}}{t_{\text{expected}}}$$

- **Sanitization:** Actual time is clamped to $t_{\text{actual}} \in [3, 1200]$ seconds to neutralize browser suspension and accidental clicks.
- **Scoring Rules:**
  - **Fast Incorrect Answer ($\rho < 0.40$ and wrong):** $E = 0.10$. Penalizes hasty guessing to encourage deliberate problem analysis.
  - **Deliberate Incorrect Answer ($\rho \ge 0.40$ and wrong):** $E = 0.35$.
  - **Optimal Correct Answer ($0.30 \le \rho \le 1.10$ and correct):** $E = 1.00$. Full efficiency reward.
  - **Slightly Overtime Correct Answer ($1.10 < \rho \le 1.80$ and correct):** $E = 0.70$.
  - **Extreme Overtime Correct Answer ($\rho > 1.80$ and correct):** $E = 0.50$.

---

## 4. Difficulty Mapping & Progression Thresholds

The continuous score $S$ maps to discrete question difficulty tiers:

```
          Easy                  Medium                  Hard
[---------------------)[-----------------------)[--------------------]
0.0                 40.0                    70.0                   100.0
```

- **$S < 40.0$:** Recommends **Easy** questions for foundational reinforcement.
- **$40.0 \le S < 70.0$:** Recommends **Medium** questions for standard campus placement technical assessments.
- **$S \ge 70.0$:** Recommends **Hard** questions for Tier-1 / product-based company interview preparation.

### Transition Safeguards:
1. **Low Confidence Clamping:** If observation count $n < 3$, confidence is classified as `low`. The engine blocks immediate transitions from uncalibrated baselines directly into `Hard` questions, enforcing at least one `Medium` verification step.
2. **Anti-Repetition:** Previously answered questions are strictly excluded from the recommendation pool.
3. **Graceful Exhaustion Fallback:** If all questions at the target difficulty tier have been completed by the student, the engine selects the closest adjacent difficulty tier (e.g., Medium if Hard is exhausted) rather than repeating questions or raising a runtime exception.

---

## 5. Factor Ablation for Research Evaluation

To scientifically validate the contribution of individual factors, the engine implements factor ablation via `estimate_proficiency_with_ablation(topic, attempts, disabled_components)`:

| Model Configuration | Disabled | Normalized Weights $(w_A, w_R, w_D, w_E)$ | Research Purpose |
|---|---|---|---|
| **Full Model** | None | $(0.45, 0.25, 0.20, 0.10)$ | Complete multi-factor adaptive recommendation |
| **No Recency ($R$-Ablated)** | `['R']` | $(0.60, 0.00, 0.27, 0.13)$ | Assesses learning rate lag when recent momentum is ignored |
| **No Efficiency ($E$-Ablated)** | `['E']` | $(0.50, 0.28, 0.22, 0.00)$ | Assesses impact of solving speed and anti-guessing penalties |
| **Accuracy-Only Baseline** | `['R', 'D', 'E']` | $(1.00, 0.00, 0.00, 0.00)$ | Conventional percentage-based question allocation |

Weights of remaining components are automatically normalized to sum to $1.00$.

---

## 6. Persistent Audit Logging & Transparency

Every time a recommendation is generated:
1. A permanent audit log is persisted in `recommendation_logs`.
2. The record stores: `user_id`, `question_id`, `question_version`, `target_topic`, `target_difficulty`, `estimated_proficiency`, `confidence_level`, `selection_reason`, `algorithm_version`, and a JSON snapshot of the learner state ($\{A, R, D, E, n\}$).
3. The student can inspect their complete recommendation audit trail via `GET /api/v1/recommendations/history` and the Settings view.

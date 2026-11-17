# Research Protocol & Evaluation Methodology

**Project Title:** AdaptivePrep: A Performance-Driven Adaptive Learning Platform for Personalized Placement Preparation  
**Study Protocol ID:** MEDICAPS-AP-2026.1  
**Affiliation:** Department of Computer Science & Engineering, Medi-Caps University, Indore  
**Document:** `/docs/RESEARCH_METHODOLOGY.md`  
**Date:** November 17, 2026  

---

## 1. Research Question & Hypotheses

### Primary Research Question
> Does dynamic, multi-factor adaptive question recommendation improve student placement test performance and practice efficiency compared to traditional accuracy-only selection and uniform random question selection?

### Null and Alternative Hypotheses
- **$H_0$ (Null Hypothesis):** There is no statistically significant difference in post-test placement scores or practice efficiency between students practicing with multi-factor adaptive recommendations and those practicing with accuracy-only or random selection.
- **$H_1$ (Alternative Hypothesis):** Students practicing with multi-factor adaptive recommendations achieve higher post-test placement score gains ($\Delta$) and greater practice efficiency within equal practice duration.

---

## 2. Experimental Design & Conditions

A three-arm randomized controlled evaluation framework is integrated directly into AdaptivePrep. Participants who provide informed consent are allocated across three study conditions in a 1:1:1 ratio:

| Condition | Strategy Identifier | Recommendation Mechanism | Primary Purpose |
|---|---|---|---|
| **Arm 1 (Experimental)** | `adaptive` | Multi-Factor $S$-Score: $S = 100 \times (0.45A + 0.25R + 0.20D + 0.10E)$ with difficulty targeting, transition safeguards, and anti-guessing penalties. | Evaluates the proposed adaptive framework. |
| **Arm 2 (Active Control)** | `accuracy_only` | Unweighted historical correctness percentage: $S_{\text{acc}} = \frac{k}{n} \times 100$. Recommends difficulty based strictly on raw percentage. | Evaluates conventional e-learning platform behavior. |
| **Arm 3 (Passive Control)** | `random` | Uniform random question selection across all topics and difficulties without regard to past student performance. | Baseline benchmark control. |

---

## 3. Factor Ablation Study Design

In addition to the three between-subject experimental arms, the backend engine supports within-system factor ablation testing to quantify the marginal value of each component in the multi-factor equation:

1. **Ablation Model 1 (Historical Accuracy Alone):** Disables $R, D, E$ ($w_A = 1.00$). Isolates baseline smoothed correctness.
2. **Ablation Model 2 (No Recency):** Disables $R$ ($w_A = 0.60, w_D = 0.27, w_E = 0.13$). Measures the effect of ignoring recent learner momentum and recovery.
3. **Ablation Model 3 (No Efficiency):** Disables $E$ ($w_A = 0.50, w_R = 0.28, w_D = 0.22$). Measures the effect of ignoring solve time and anti-guessing penalties.
4. **Full Model:** All 4 factors enabled ($w_A = 0.45, w_R = 0.25, w_D = 0.20, w_E = 0.10$).

---

## 4. Evaluation Protocol Workflow

```mermaid
sequenceDiagram
    autonumber
    actor Participant as Student Cohort
    participant System as AdaptivePrep Platform
    participant DB as Research Database
    participant Analyst as Research Exporter

    Participant->>System: Register / Login with Consent Toggle
    System->>DB: Assign Pseudonym Code (e.g. PART-1014-ADAP) & Arm (1:1:1)
    Participant->>System: Phase 1: Baseline Diagnostic Pre-Test (10 Questions)
    System->>DB: Store Pre-Test Score (Score_pre)
    Note over Participant,System: Phase 2: Intervention Practice (3 Guided Sessions)
    Participant->>System: Solves Questions under Assigned Strategy
    System->>DB: Record Attempts, Duration, and Algorithmic Logs
    Participant->>System: Phase 3: Post-Intervention Assessment (10 Questions)
    System->>DB: Store Post-Test Score (Score_post)
    System->>DB: Compute Delta = Score_post - Score_pre
    Analyst->>System: GET /api/v1/research/studies/1/export
    System-->>Analyst: Pseudonymized CSV Dataset for Statistical Analysis
```

### Protocol Steps:
1. **Recruitment & Informed Consent:** Students opt-in via registration or Settings. A unique participant code (e.g., `PART-1001-ADAP`, `PART-1002-ACC`, `PART-1003-RND`) is generated. Personal identifying information (name, email) is decoupled.
2. **Pre-Intervention Baseline (Pre-Test):** A standardized 10-question placement assessment spanning Data Structures, Algorithms, DBMS, Operating Systems, and Networks.
3. **Practice Intervention Phase:** A minimum of 3 practice sessions (30 questions total) served according to the assigned strategy arm.
4. **Post-Intervention Assessment (Post-Test):** An equivalent 10-question placement examination measuring final topic mastery.
5. **Statistical Synthesis:** Computation of individual score gains, completion latency, and group aggregates.

---

## 5. Statistical Evaluation Metrics

- **Absolute Score Gain ($\Delta$):**
  $$\Delta = \text{Score}_{\text{post}} - \text{Score}_{\text{pre}}$$
- **Relative Percentage Gain ($g$):**
  $$g = \frac{\text{Score}_{\text{post}} - \text{Score}_{\text{pre}}}{\text{Score}_{\text{pre}}} \times 100\%$$
- **Effect Size (Cohen's $d$):**
  $$d = \frac{\bar{\Delta}_{\text{adaptive}} - \bar{\Delta}_{\text{control}}}{s_{\text{pooled}}}$$
  Where $s_{\text{pooled}}$ is the pooled standard deviation across cohorts.
- **Solving Efficiency ($\bar{t}$):** Mean seconds per question attempted during intervention.
- **Protocol Retention Rate:** Percentage of participants completing both pre- and post-tests.

---

## 6. Pseudonymized Dataset Schema (CSV Export)

When researchers invoke `GET /api/v1/research/studies/{id}/export`, AdaptivePrep produces a compliant CSV containing the following fields:

| Column Name | Data Type | Description | Privacy Safeguard |
|---|---|---|---|
| `participant_code` | String | Format: `PART-XXXX-STRAT` | De-identified pseudonymous key |
| `assigned_strategy` | Categorical | `adaptive`, `accuracy_only`, `random` | Experimental arm |
| `pre_test_score` | Float | Percentage score on pre-test ($0-100$) | Aggregated score |
| `post_test_score` | Float | Percentage score on post-test ($0-100$) | Aggregated score |
| `score_gain_percentage_points` | Float | Post-test score minus pre-test score | Derived metric |
| `relative_gain_percent` | Float | Percentage improvement relative to baseline | Derived metric |
| `intervention_practice_attempts` | Integer | Total questions practiced during study | Interaction count |
| `avg_solving_time_seconds` | Float | Mean solving time across attempts | Telemetry metric |
| `completion_status` | Boolean | True if both pre and post tests completed | Study validity indicator |

**Privacy Verification:** Automated tests (`test_research_pseudonymized_export`) strictly verify that no student names, email addresses, or database primary keys appear in the export output.

---

## 7. Research Ethics, Limitations & Academic Disclaimer

- **Institutional Oversight:** Designed according to standard academic research guidelines for educational software evaluation at Medi-Caps University.
- **Voluntary Participation:** Students can withdraw consent or opt-out at any time via the Settings panel without affecting their access to practice materials.
- **Academic Disclaimer:** Demo datasets pre-seeded in the local development environment are generated for software and statistical pipeline verification. They must not be cited as empirical proof of pedagogical superiority until formal clinical field trials with enrolled student cohorts are conducted.

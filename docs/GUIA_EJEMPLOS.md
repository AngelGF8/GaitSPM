# Guide to the eight examples

Results calculated on 24 October 2026 with GaitSPM 1.4.0 / spm1d 0.4.53 and fixed seeds. Each example contains 30 synthetic cases and 30 synthetic controls. These are analysis exercises, not conclusions about real patients.

Workflow: load → review mapping and quality → configure → run → read interpretation and details → export. Defaults: all example variables, side L, α=0.05 and Bonferroni correction across variables. Two groups: Welch. Repeated measurements: cases only, with the same participant IDs.
## 01_fai · Symptomatic FAI

**Design:** `ttest2`. **Groups:** ['Control', 'FAIS']. **Filter:** none. **Conditions:** BASE.

| Variable | Included n | Confirmed clusters (% cycle; adjusted p) |
|---|---|---|
| HipFlexion | 30 / 30 | None |
| HipAdduction | 30 / 30 | None |
| HipRotation | 30 / 30 | None |

**What to look for:** Distinguish visual differences from a statistical contrast exceeding the threshold. No variable has confirmed clusters with this recipe; this does not demonstrate equivalence.

**Files:** `datasets/synthetic/01_fai/01_fai.csv` and `.xlsx`. ROM and mean formulas in Metrics update when Curves_Wide is edited; SPM results are recalculated in GaitSPM.

## 02_knee_oa · Knee osteoarthritis

**Design:** `ttest2`. **Groups:** ['Control', 'KOA']. **Filter:** none. **Conditions:** BASE.

| Variable | Included n | Confirmed clusters (% cycle; adjusted p) |
|---|---|---|
| HipFlexion | 30 / 30 | 0.0–0.8%; p=0.050; 67.0–72.5%; p=0.049; 87.3–95.7%; p=0.048; 98.9–100.0%; p=0.050 |
| KneeFlexion | 30 / 30 | 0.0–100.0%; p<0.001 |
| AnkleDorsiflexion | 30 / 30 | None |

**What to look for:** Locate regions exceeding the threshold and compare them with the mean curves. Check which variables are not significant and the contrast sign before interpreting direction. The mean magnitude shown within a cluster is descriptive.

**Files:** `datasets/synthetic/02_knee_oa/02_knee_oa.csv` and `.xlsx`. ROM and mean formulas in Metrics update when Curves_Wide is edited; SPM results are recalculated in GaitSPM.

## 03_hip_oa · Hip osteoarthritis

**Design:** `ttest2`. **Groups:** ['Control', 'HOA']. **Filter:** none. **Conditions:** BASE.

| Variable | Included n | Confirmed clusters (% cycle; adjusted p) |
|---|---|---|
| HipFlexion | 30 / 30 | 0.0–39.2%; p<0.001; 51.9–100.0%; p<0.001 |
| HipAdduction | 30 / 30 | 0.0–59.7%; p<0.001; 83.7–100.0%; p=0.017 |
| HipRotation | 30 / 30 | 0.0–53.3%; p<0.001; 82.0–100.0%; p=0.002 |

**What to look for:** Locate regions exceeding the threshold and compare them with the mean curves. Check which variables are not significant and the contrast sign before interpreting direction. The mean magnitude shown within a cluster is descriptive.

**Files:** `datasets/synthetic/03_hip_oa/03_hip_oa.csv` and `.xlsx`. ROM and mean formulas in Metrics update when Curves_Wide is edited; SPM results are recalculated in GaitSPM.

## 04_multiple_sclerosis · Multiple sclerosis

**Design:** `ttest2`. **Groups:** ['Control', 'MS']. **Filter:** none. **Conditions:** BASE.

| Variable | Included n | Confirmed clusters (% cycle; adjusted p) |
|---|---|---|
| HipFlexion | 30 / 30 | None |
| KneeFlexion | 30 / 30 | 81.3–88.4%; p=0.022 |
| AnkleDorsiflexion | 30 / 30 | 0.0–56.0%; p<0.001; 65.3–100.0%; p<0.001 |

**What to look for:** Locate regions exceeding the threshold and compare them with the mean curves. Check which variables are not significant and the contrast sign before interpreting direction. The mean magnitude shown within a cluster is descriptive.

**Files:** `datasets/synthetic/04_multiple_sclerosis/04_multiple_sclerosis.csv` and `.xlsx`. ROM and mean formulas in Metrics update when Curves_Wide is edited; SPM results are recalculated in GaitSPM.

## 05_hip_arthroplasty · Hip arthroplasty

**Design:** `ttest2`. **Groups:** ['Control', 'THA']. **Filter:** none. **Conditions:** BASE.

| Variable | Included n | Confirmed clusters (% cycle; adjusted p) |
|---|---|---|
| HipFlexion | 30 / 30 | 0.0–33.6%; p<0.001; 56.1–100.0%; p<0.001 |
| HipAdduction | 30 / 30 | 0.0–57.3%; p<0.001; 90.3–100.0%; p=0.034 |
| HipRotation | 30 / 30 | None |

**What to look for:** Locate regions exceeding the threshold and compare them with the mean curves. Check which variables are not significant and the contrast sign before interpreting direction. The mean magnitude shown within a cluster is descriptive.

**Files:** `datasets/synthetic/05_hip_arthroplasty/05_hip_arthroplasty.csv` and `.xlsx`. ROM and mean formulas in Metrics update when Curves_Wide is edited; SPM results are recalculated in GaitSPM.

## 06_acl · ACL reconstruction

**Design:** `ttest2`. **Groups:** ['Control', 'ACLR']. **Filter:** none. **Conditions:** BASE.

| Variable | Included n | Confirmed clusters (% cycle; adjusted p) |
|---|---|---|
| HipFlexion | 30 / 30 | 0.0–100.0%; p<0.001 |
| KneeFlexion | 30 / 30 | None |

**What to look for:** Locate regions exceeding the threshold and compare them with the mean curves. Check which variables are not significant and the contrast sign before interpreting direction. The mean magnitude shown within a cluster is descriptive.

**Files:** `datasets/synthetic/06_acl/06_acl.csv` and `.xlsx`. ROM and mean formulas in Metrics update when Curves_Wide is edited; SPM results are recalculated in GaitSPM.

## 07_ms_fatigue · Multiple sclerosis · fatigue and recovery

**Design:** `anova1rm`. **Groups:** None. **Filter:** MS. **Conditions:** ['BASE', 'FATIGUE', 'RECOVERY'].

| Variable | Included n | Confirmed clusters (% cycle; adjusted p) |
|---|---|---|
| HipFlexion | 30 / 30 / 30 | 48.0–89.4%; p<0.001 |
| KneeFlexion | 30 / 30 / 30 | 44.4–91.9%; p<0.001 |
| AnkleDorsiflexion | 30 / 30 / 30 | 47.3–88.1%; p<0.001 |

**What to look for:** Identify an overall effect across BASE, FATIGUE and RECOVERY. Inspect post hoc comparisons to locate the pairs. All three conditions belong to the same 30 cases, not 90 patients. The change was deliberately introduced in the generator and does not represent clinical efficacy.

**Files:** `datasets/synthetic/07_ms_fatigue/07_ms_fatigue.csv` and `.xlsx`. ROM and mean formulas in Metrics update when Curves_Wide is edited; SPM results are recalculated in GaitSPM.

## 08_acl_retest · ACL · retest without systematic change

**Design:** `paired_cond`. **Groups:** None. **Filter:** ACLR. **Conditions:** ['TEST', 'RETEST'].

| Variable | Included n | Confirmed clusters (% cycle; adjusted p) |
|---|---|---|
| HipFlexion | 30 / 30 | None |
| KneeFlexion | 30 / 30 | None |

**What to look for:** Compare TEST and RETEST with pairing by ID. The generator includes measurement noise but no systematic shift. There are no significant clusters with this recipe. This does not establish reliability or equivalence; those objectives require dedicated designs and measures.

**Files:** `datasets/synthetic/08_acl_retest/08_acl_retest.csv` and `.xlsx`. ROM and mean formulas in Metrics update when Curves_Wide is edited; SPM results are recalculated in GaitSPM.

## Simulation assumptions

Examples 01–06 match scalar means and SDs retained from version 1.3 using standardized quantiles; they are not independent, identically distributed patient samples. Shapes, smoothness, phases and correlations are imposed. Examples 07/08 add hypothetical changes and noise. Example 05 represents a post-arthroplasty context, not a seventh pathology. All 480 IDs are unique across datasets. Sources and limitations are documented in references/README.md and each metadata.json.

Results in this guide apply only to the original files and their recipes. Changing variables, groups, correction, side or method changes the results. Save the analysis JSON to retain its configuration.

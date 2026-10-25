# Simulation sources and assumptions

Units: degrees. All **34 mean/SD pairs** are in `datasets/synthetic/calibration_all.csv`. Each dataset includes metadata describing its population, anchors and assumptions.

| Dataset | Primary source and table | Parameters |
| --- | --- | --- |
| FAI | [Hao 2025](https://doi.org/10.1186/s12891-025-08727-4), table 2, FAIS without BDDH | Three hip ranges of motion |
| Knee OA | [Huang 2008](https://doi.org/10.1016/j.medengphy.2008.02.006), table 3 | Hip/knee T1 and ankle T3 |
| Hip OA | [Bahr 2021](https://doi.org/10.12659/MSM.934558), table 2 PreOP | Three hip ranges of motion |
| MS | [Lencioni 2016](https://doi.org/10.3389/fnhum.2016.00620), table 1 | Sagittal hip, knee and ankle ROM |
| Arthroplasty | [Bahr 2021](https://doi.org/10.12659/MSM.934558), table 2 PostOP | Three hip ranges of motion |
| ACL | [Noehren 2013](https://pmc.ncbi.nlm.nih.gov/articles/PMC4313379/), table 2 WALK | Hip/knee flexion at initial contact; walking, not running |

Control versus case examples:

- FAI sagittal hip ROM: 46.86 ± 3.79 versus 46.11 ± 5.82.
- Knee OA, hip T1: 27.57 ± 4.66 versus 22.77 ± 7.47.
- Hip OA sagittal ROM: 43.61 ± 4.78 versus 25.27 ± 9.93.
- MS knee ROM: 56 ± 5 versus 46 ± 15.
- Arthroplasty sagittal hip ROM: 43.61 ± 4.78 versus 33.14 ± 8.55.
- ACL hip flexion: 26.1 ± 7.4 versus 20.0 ± 7.4. Knee signs are reversed to make flexion positive; SD is unchanged.

## Scope

The teaching sample size is n=60 (30 per group), not the original study sample size. Thirty standardized quantiles per group match the sample mean and SD (ddof=1). Rescaled lognormal quantiles are used where ROM would otherwise be negative. These are not independent, identically distributed clinical observations. PCHIP shapes, offsets, phases, smooth noise with sigma=4 nodes and correlations are assumed. A ROM value does not identify a complete trajectory.

Phase values are imposed at specified synthetic nodes. ACL anchors are assigned to nodes 0 and 12 as a technical exercise, without claiming that the source measured those instants. Individual peaks are not reconstructed.

MS represents slow walking (mean EDSS 5.8), not the whole disease spectrum. Symptomatic FAI is not equivalent to asymptomatic cam morphology. The Bahr examples are independent: **do not pair 03 and 05 or infer recovery**. `technical_score` is random and has no clinical meaning. L denotes a simulated index side, not the original studies' laterality.

Clusters in these artificial curves do not replicate clinical results or support diagnostic conclusions. Published tables calibrate scalar values, not every curve node.

## Examples 07 and 08, added in 1.4

These reuse the MS and ACL contexts with new IDs. Fatigue/recovery and technical retesting are hypothetical scenarios. Change amplitudes, correlations between measurements and the absence of a systematic effect in 08 are teaching assumptions, not published data. Each example retains 30 cases and 30 controls; the recommended design analyzes repeated conditions in the 30 cases.

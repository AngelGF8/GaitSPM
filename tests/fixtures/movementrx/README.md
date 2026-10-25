# External CSV: MovementRx

**Independent source:** https://github.com/aalhossary/MovementRx, commit `70f97b52b55e476fa52f9e733a98cefe55532c18`.

Original file: `spmclient/res/refData/kinematic/L_KneeX_Ang_Ref.csv`. It is preserved unchanged in `original/`; its Git blob SHA-1 is `b971c393d1fa5219e49ba7755ce784189e36c4f8`. The upstream GPL v3 license is retained in LICENSE and the original README in UPSTREAM_README.md.

Article: Alhossary A, Pataky T, Ang WT, Chua KSG, Kwong WH, Donnelly CJ. Versatile clinical movement analysis using statistical parametric mapping in MovementRx. Scientific Reports. 2023;13:2414. https://doi.org/10.1038/s41598-023-29635-4

The article describes a trial-averaged curve per participant in the reference files. This CSV contains 20 rows and 101 left-knee angles in the X/sagittal plane. The original sign convention is preserved. No trajectories are reconstructed or simulated.

## Explicit adaptation

The original has columns V1…V100 and a final blank header. It has no identifiers or groups, so **it cannot be imported directly as a valid participant dataset**. GaitSPM rejects missing IDs; an angle column must not be used as an identifier.

`movementrx_import_test.csv` adds row IDs MRX01…MRX20, condition REFERENCE and side L, and renames the 101 nodes KneeSagittal_0…100. Alternating rows receive TestA/TestB labels, with 10 per label. This arbitrary split is solely a software test: **it does not represent diagnoses or interventions**. All curve values are identical to the original (maximum difference 0).

The test compares these labels using Welch's test to verify the software, not to draw a clinical conclusion. There are no significant clusters under this configuration; this does not demonstrate equivalence. Keep this software check separate from the eight synthetic examples with 30+30 participants.

## Reproduce in GaitSPM

1. Run `python launch.py` and load `movementrx_import_test.csv`.
2. Map subject → ID, group → group, condition → condition and side → side.
3. Check 20 participants, TestA=10/TestB=10, 101 nodes and KneeSagittal → knee/sagittal; confirm units and mapping.
4. Select two independent groups, TestA/TestB, REFERENCE, L only, parametric, equal variances disabled (Welch), two-tailed, α=0.05 and Bonferroni.
5. Run and export. The automated test generates `.test-output/external/external-result.png`; this temporary output is not versioned.

Recreate the adaptation: `python scripts/prepare_external_csv.py`. Reproducible test with real HTTP upload: `python tests/test_external_upload.py`.

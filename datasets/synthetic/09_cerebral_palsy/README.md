# Cerebral palsy · crouch gait

Fixed synthetic teaching dataset: 30 controls and 30 CP cases, 12 angular variables covering pelvis, hip, knee and ankle, 101 nodes (0–100% gait cycle), degrees, one indexed limb (L), condition BASE.

Load `09_cerebral_palsy.csv` or the `Curves_Wide` sheet of the original workbook. The app's example button loads these same CSV values in both native and browser modes. The original files are preserved; changing the generator seed does not change this fixed example.

Recommended analysis: independent groups (Control vs CP), Welch, two-tailed, alpha 0.05, Bonferroni across 12 fields. `technical_score` is a teaching covariate without clinical meaning.

This is a hypothetical model, not patient data or a reproduction of published effect sizes. Shapes, timing and covariance are assumed. The workbook cites [Abbasi et al. (2018)](https://pmc.ncbi.nlm.nih.gov/articles/PMC6169120/) for qualitative context only. Cluster locations and p-values describe this simulation, not that publication. File checksums and the analysis recipe are in `metadata.json`.

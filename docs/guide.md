# Clinical research guide

Start with the scientific question and participant structure. GaitSPM analyses prepared curves; it does not detect gait events, reconstruct joint angles from sensors, diagnose disease or establish clinical importance.

1. Segment and normalise each cycle to 101 points. Document the reference frame, units, side, walking speed and trial aggregation.
2. Assign a stable ID to each participant. The same participant retains the same ID across conditions. Different participants never share IDs, even across groups.
3. Upload a wide CSV with metadata and `HipFlexion_0` through `HipFlexion_100`, or use the documented long or transposed formats. Inspect mapping and quality checks before analysis.
4. Define groups, conditions, variables, alpha and correction before examining significance. Review [statistical designs](statistics.md).
5. Check complete-case exclusions, balance and sample sizes. Missing data can change the population being analysed.
6. Export SVG or PDF for vector figures, CSV/XLSX for results and JSON for configuration. Preserve the source data, software version and analysis configuration.

For group differences adjusted for walking speed, select ANCOVA and a numeric speed column. Each participant must contribute one selected condition. The two-group contrast is second selected group minus first; covariates are centered on complete cases. Common slopes and equal residual variance are assumptions, not results of an automatic check. The displayed mean curve is unadjusted.

For group × repeated condition, select mixed ANOVA. Select the interaction to ask whether changes across conditions differ by group. Do not infer an interaction from a significant within-group comparison in only one group.

A nonsignificant field is not evidence of equivalence. Pointwise uncertainty bands are not simultaneous confidence bands. Cluster p-values describe SPM cluster inference, not separate tests at each gait-cycle percentage.

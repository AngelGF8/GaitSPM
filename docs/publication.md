# Publication and outreach

## Release and citation

`CITATION.cff` describes the last released version. Keep it synchronized with the tag and actual release date; do not label unreleased work as a published version. The `Unreleased` changelog describes this update.

1. Run all native, UI and concordance checks on the exact release commit; record the software test status.
2. Build documentation and review the browser and Streamlit workflows with synthetic data.
3. Update version, citation and changelog; tag the stable version. The release workflow runs tests and prepares an archive plus a draft GitHub release. The workflow attaches the verified artifacts; publish the draft after review.
4. Enable the repository in the author's Zenodo account and archive the GitHub release. Verify its version DOI and concept DOI before adding the badge or identifier to citation metadata. See [Zenodo GitHub integration](https://help.zenodo.org/docs/github/).
5. Repeat the archive verification for every release. A GitHub workflow cannot itself grant access to the author's Zenodo account.

## Hosting and repository settings

Pages: select GitHub Actions in Settings → Pages, then run the Pages workflow. Documentation is served at the site root and Pyodide at `/app/`. Test file upload, inference and download in an actual browser before describing the hosted mode as validated.

Streamlit Community Cloud: create an app from this repository with entrypoint `app/gaitspm_app.py`. Its adjacent `app/requirements.txt` includes the optional Streamlit dependencies through `requirements-streamlit.txt`. Configure cloud dependencies appropriately and publish the resulting URL only after its smoke test. Hosted uploads run remotely.

Repository settings: add topics `biomechanics`, `gait-analysis`, `spm1d`, `statistical-parametric-mapping`, `pyodide`, `streamlit`; enable Discussions; add a concise description and the verified documentation URL. Upload `docs/assets/social-preview.png` in General settings. Use the `good first issue` label on scoped, actionable contributor tasks.

At inspection on 2026-10-25, GitHub reported Pages and Discussions disabled, no topics, and repository creation on 2026-10-24. This local update does not by itself change those settings.

## Journal preparation

Research manuscripts and their results are maintained separately. [Current JOSS submission requirements](https://joss.readthedocs.io/en/latest/submitting.html) include sustained public development for more than six months and demonstrated research use, plus disclosure of AI assistance. A recently created repository cannot meet the public-history criterion immediately. Record actual applications and community feedback as they occur; consider SoftwareX after checking its current scope and instructions.

Author review must supply affiliation, ORCID if available, funding/conflicts, research-use evidence and a truthful statement of human validation. Do not invent adopters or scientific results. Software concordance does not establish clinical validity.

## Outreach materials

`outreach/drafts.md` contains unsent drafts for Todd Pataky, Biomch-L and social channels. Link a stable release, executable tests and an openly reproducible tutorial before inviting adoption. Track replies through issues only with the sender's permission. A request for a listing is not an endorsement.

A real-data two-minute demo should show CSV provenance, mapping, design, SPM output and export, and identify whether the grouping is scientific or a test partition. Existing screenshots  are presentation assets, not evidence that a new real-data demonstration has been recorded.

Poster/demo candidates are ISB, ESMAC, GCMAS and SIBB; check their official current calls before committing dates or fees. For a FAIS application paper, preregister the question, dataset eligibility, covariates and correction; obtain appropriate data access and independently assess design and interpretation.

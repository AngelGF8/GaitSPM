# Frequently asked questions

## Is this a new statistical engine?

No. GaitSPM prepares data and calls spm1d. Its numerical suite checks that preparation and inference agree with direct upstream calls. Cite GaitSPM and the applicable spm1d methods separately.

## Where do my data go?

Native mode processes data on your computer. Pyodide mode processes data in your browser after downloading dependencies. Streamlit Community Cloud would process data on a remote server; use synthetic or suitably shareable data there. Uploaded files in native mode are temporary and removed at normal shutdown.

## Why is a factorial design rejected?

Check for incomplete participants, unequal cell sizes, reused IDs in an independent design, fewer than three participants per cell, or unsupported variance/inference options. Use mixed ANOVA for repeated conditions. Do not relabel repeated participants to bypass the check.

## Why does ANCOVA show an unadjusted mean?

Its SPM t-field tests the adjusted coefficient. The mean plot is a descriptive summary of complete cases, not estimated marginal means. The label makes this explicit.

## Does identical software output validate a scientific conclusion?

No. Agreement within numerical precision verifies the implementation on tested data. It does not establish appropriate design, preprocessing, assumptions, clinical validity or usefulness of an effect.

## Can I use vector figures?

Yes: SVG and PDF are already available. Preserve labels, units, correction and version in the figure caption.

## Is JOSS submission or a DOI already available?

No new submission or DOI is claimed by this development update. Follow the [publication checklist](publication.md); only display DOI and journal badges once they resolve to a genuine record.

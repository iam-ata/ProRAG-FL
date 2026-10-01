---
trigger: always_on
description: Keeps implementation/results separate from the LaTeX manuscript until paper-export phase.
---

# Manuscript Boundary

The manuscript is a sibling project directory.

Normal implementation phases must not edit it.

Generated results first go to:
`Code/reports/paper_exports/`.

Only the explicit paper-sync phase may copy verified generated tables/figures to the manuscript.

Do not read numerical values from manuscript prose as experiment input.

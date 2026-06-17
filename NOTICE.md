# NOTICE — data & attribution

## Competition data is NOT included

This repository contains **reproduction code, documentation, and checksums only**. It does
**not** redistribute the competition dataset, the engineered features, or the prediction
CSVs. The Sea Winds Predictions Phase-1 dataset is the property of the competition organizers
and is provided under the terms of the competition / its Zenodo record. Download it from the
official sources:

- Competition (Codabench #13821): <https://www.codabench.org/competitions/13821/>
- Starting kit: <https://github.com/DavidMedernach/Hackathon-Sea-Winds-Predictions>
- Dataset (`phase1_dataset.zip`): <https://zenodo.org/records/19538994>

Please honor the competition's data-use terms (the competition prohibits external data for
the modeling task; the dataset license governs reuse).

## The submission artifact

`submission_FINAL_BEST.zip` (attached to this repository's GitHub Release) is the author's own
competition output — the predictions produced by the pipeline in this repository. Its `sha256`
checksums are pinned in [`CHECKSUMS.md`](CHECKSUMS.md).

## Code

Reproduction and pipeline code in this repository is released under the MIT License
([`LICENSE`](LICENSE)). Portions of the heavy-base code under `pipeline/heavy/` are derived
from the competition's public starting kit and remain subject to the starting kit's terms.

## Scope

This is a curated, public **reproduction** package. Competition-day leaderboard-operations
material (live-board monitoring, defensive playbooks) has been intentionally omitted; the
technical method, the build pipeline, and the full version-by-version logbook are included.

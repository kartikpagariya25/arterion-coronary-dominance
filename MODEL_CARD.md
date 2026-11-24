# Model card: Arterion Coronary Dominance

> Research prototype, not a medical device. Do not use for diagnosis or treatment decisions.

## Task
Right- or left-dominance prediction from the right- and left-coronary angiogram runs of one study.

## Model
DominanceNet: a shared ResNet-18 frame encoder, a learned RCA/LCA view embedding and an MLP; study logits are the mean over runs (11.2 M parameters, ONNX).

## Input and output
- **Input:** 1-8 angiogram runs, each tagged RCA or LCA (video, .npz with a pixel_array, or a single image).
- **Output:** dominance type, confidence, p(left), the views used and a per-run breakdown.

## Training and evaluation data
CoronaryDominance (Kruzhilov et al., Scientific Data 2025, CC0-1.0), main_normal subset: 779 studies, split 70/15/15 at study level.

## Results
- Held-out 117 studies, up to 4 runs per study: AUROC 0.996, balanced accuracy 0.961.
- One RCA run plus one LCA run: AUROC 0.987, balanced accuracy 0.943.
- One run of a single view: balanced accuracy 0.936 (RCA) and 0.884 (LCA).

Numbers in `training/artifacts/metrics.json` match the published weights.

## Limitations
- Studies are anonymised, so several studies of one patient may sit on both sides of the split; the figures may be optimistic.
- Single-centre data; not evaluated on the dataset's real_distribution or domain_shift sets.
- Left-dominant studies are the minority class (251 of 779).

## Intended use
Research, teaching and prototyping. Not for diagnosis, triage or any clinical decision, and not validated for any clinical setting.

## Licence and data terms
Code: MIT. The dataset is CC0-1.0.

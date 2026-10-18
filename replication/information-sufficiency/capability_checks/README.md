# Capability checks of Supplementary Section S11

Supplementary Section S11 compares AIMNER by capability with the pre-construction steps that four downstream
data-fusion families document. Its explanations of the "no" cells quote numerical examples. The four scripts in
this folder compute every one of these numbers.

| Script | Section | Table |
|---|---|---|
| `f05_multiview_representation.py` | S11.1, multiview latent or coordinated representation | S11 Table A |
| `f06_similarity_kernel_fusion.py` | S11.2, similarity-network and multiple-kernel fusion | S11 Table B |
| `f07_state_estimation.py` | S11.3, dynamic state estimation and assimilation | S11 Table C |
| `f13_layer_reduction.py` | S11.4, multilayer-network layer reduction | S11 Table D |

Each output line names the row of the S11 table, the capability and the quantity shown. The docstring of each
script describes its examples: the node sets, the shocks and the constructed counterexamples.

## Software

Python 3.12 or later with numpy. The scripts use no other package, read no data file and need no internet
access.

## Run

From this folder, for example:

    python f05_multiview_representation.py > f05_multiview_representation_output.txt

The scripts are deterministic, with fixed seeds. Each run reproduces the packaged file `<script>_output.txt`.
The packaged outputs were written on Windows with Python 3.14.6 and numpy 2.5.4. On other systems they can differ
in their line endings and in the last digits of values that are zero up to rounding.

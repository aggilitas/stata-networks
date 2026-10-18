# Replication package

**Information sufficiency criteria for exactness under partial observation in the AIMNER framework**
Necmi Talay, Hakan Acaroğlu, Aslıhan Günal and Fausto Pedro García Márquez
(corresponding author)

Supplementary Software 1. The package reproduces every numerical result of the
application and of the synthetic design of the paper, from the published data
as used. The application covers the export networks of the EU textile,
clothing, leather and footwear (TCLF) chapters, the layers of one multiplex,
built with the AIMNER flow and attribute constructions (Talay et al., 2026)
through the Stata command `network_calc` of the netcalc package (Talay, 2026)
with REST, the aggregate of the rest of the network.

Scope: 18 member states (BE BG DE DK EE ES FR GR HR HU IT LT LV PL PT RO SE
SI), 18 HS chapters (41-43, 50-54, 56-65), 2016-2025, exporter declarations
only (Eurostat Comext DS-045409). The data cover the 19 TCLF chapters 41-43
and 50-65 for the 27 member states; step 1 selects the member states and the
chapters (Section 4.2).

The source data are included as used, and the package runs without internet
access. The package does not include the scripts that retrieved the data; the
requests are listed under Data sources.

## Contents

```
README.md
LICENSE                             Academic and Research Use License (the netcalc licence)
data/                               source data as used
  comext_exports/export_XX.csv.gz   exporter declarations, 27 EU reporters, 19 TCLF chapters
  comext_imports/import_XX.csv.gz   importer declarations, ten reporters, 19 TCLF chapters (step 4)
  eurostat/namq_10_a10_C_r20.json, namq_10_a10_e_C_r20.json   quarterly national accounts, NACE C
  eurostat/nama_10_a64_eu27.json, nama_10_a64_e_eu27.json     annual industry accounts, NACE C
  eurostat/sts_inpp_a_C_eu27.json   producer prices, NACE C
  eurostat/nrg_pc_205_eu27.json     electricity prices for non-household consumers
  ecb_mir/MIR_A2Z_XX.csv            ECB MFI interest rates, one file for each of twenty member states
1_selection/
  select_subnet.py                  member states and chapters observed in 2016-2025
  selection_result.txt
  window_check.py                   the same rule over longer windows, 2006-2025 to 2016-2025
  window_check_result.txt
2_attributes/
  real_credit_cost.py               real cost of bank credit to non-financial corporations
  real_credit_cost.csv, real_credit_cost_flags.txt
  manufacturing_productivity.py     manufacturing value added per hour worked, quarterly accounts
  manufacturing_productivity.csv, manufacturing_productivity_check.txt
3_inputs/
  build_inputs.py                   builds the input files of the do-file
  networks/                         one file per network: export_<hs>.csv (18), attr_prod.csv, attr_fin.csv, attr_elec.csv
  check_weights.csv                 weights x_ij / X_i by the direct formula, for the check in estimation.do
  input_notes.txt                   zero cells of the export inputs; flags of the electricity and finance inputs
4_declaration_check/
  compare_declarations.py           exporter- against importer-declared weights
  compare_declarations_result.txt
5_estimation/
  estimation.do                     Stata: construction with network_calc, checks, unit roots, the 306 models
  estimation.log                    log of the run that produced the results
  mrqap.py                          MRQAP inference for the 306 models
  mrqap_precision.py                Monte Carlo precision of the MRQAP p values; 100,000 draws near 0.05
  qv_sensitivity.py                 sensitivity to exports declared without an importer (QV)
  layer_positions.py                positional analysis of the second network
  layer_network_figure.py           Fig. 3, the second network
  multiple_testing.py               the second network under corrections for multiple testing
  specification_sensitivity.py      the tests under year effects and other level/change choices
  descriptive_statistics.py         descriptive statistics
  descriptive_statistics_result.txt
  results/unit_roots.csv, screen_models.csv                 written by estimation.do
  results/mrqap.csv, mrqap_summary.txt                      written by mrqap.py
  results/mrqap_precision.csv, mrqap_precision.txt          written by mrqap_precision.py
  results/qv_sensitivity.txt, qv_sensitivity_cells.csv      written by qv_sensitivity.py
  results/layer_positions.txt, layer_pair_relations.csv    written by layer_positions.py
  results/fig_layer_network.pdf                             written by layer_network_figure.py
  results/multiple_testing.txt                              written by multiple_testing.py
  results/specification_sensitivity.txt                     written by specification_sensitivity.py
6_synthetic/
  synthetic_experiments.py          synthetic design and the examples of Propositions 5-7
  synthetic_results.json, figure1_boundary.pdf
../netcalc/                         netcalc 2.0.0 at commit 6012f3f, next to this folder (see INSTALL.txt there)
```

The folders are numbered in run order.
The structure is to be kept: every Python script finds its files from its own
location, so it can be started from any working directory, and the do-file is
run from `5_estimation`.

## Software

- **Python 3.12 or later**, standard library only, for steps 1-4 and 9. From
  Python 3.12 on, `sum()` of floats uses Neumaier summation; under an older
  Python, some values of the attribute files differ from the packaged ones in
  the last binary digit.
- **Python with numpy, scipy and matplotlib** for steps 6-8, and with numpy,
  networkx, sympy and matplotlib for step 10. The packaged results were
  produced with Python 3.9.21, numpy 2.0.2, scipy 1.13.1, networkx 3.2.1,
  matplotlib 3.8.4 and sympy 1.13.1 on Windows 10.
- **Stata 17** (the do-file sets `version 17`) for step 5, with:
  - `network_calc` 2.0.0, netcalc package (Talay, 2026), at commit
    6012f3f6b2363e2881ab98a22ac420216ce869c6 (23 September 2026) of
    https://github.com/aggilitas/stata-networks:
    `net install netcalc, from("https://raw.githubusercontent.com/aggilitas/stata-networks/6012f3f6b2363e2881ab98a22ac420216ce869c6/")`,
    or offline from the folder `netcalc` of this archive:
    `net install netcalc, from("<full path to the netcalc folder>") replace`.
    Method 1b of `netcalc/README.md` installs the version used for the earlier
    Knowledge-Based Systems article, not the version used here, and the
    `examples/` folder that README describes is not part of this archive.
  - `reghdfe` 6.12.5 and `ftools` 2.49.1, e.g.
    `net install reghdfe, from("https://raw.githubusercontent.com/sergiocorreia/reghdfe/master/src/")`,
    and likewise for `ftools`. The install hint that the do-file prints when a
    package is missing says `ssc install`; use these sources instead.

No other installation is needed. Installing the three Stata packages with
`net install` and the Python libraries with `pip` takes a few minutes on a
desktop computer.

## Run order

From the package folder (the folder that holds this README):

1. **Selection.** `python 1_selection/select_subnet.py` applies the
   observation rule of Section 4.2 and reports the
   member states observed in every chapter, the trade-off between the number of
   chapters and the number of member states, and the largest share of exports
   declared without an importer of every member state, with the gap in which
   the 1% threshold falls. `python 1_selection/window_check.py` applies the
   same rule to every window from 2006-2025 to 2016-2025.
2. **Attributes.** `python 2_attributes/real_credit_cost.py` and
   `python 2_attributes/manufacturing_productivity.py`.
3. **Inputs.** `python 3_inputs/build_inputs.py`, after step 2.
4. **Declaration check.** `python 4_declaration_check/compare_declarations.py`.
5. **Stata.** In Stata: `cd "<package folder>/5_estimation"` and
   `do estimation.do` (about a minute). It writes `estimation.log`,
   `results/unit_roots` and `results/screen_models`.
6. **MRQAP.** `python 5_estimation/mrqap.py` (about five minutes): the MRQAP
   p values (10,000 node permutations, seed 20260927) of the flow weight and
   of each attribute edge value; it checks that its coefficients, clustered
   standard errors and p values equal those of `results/screen_models.csv`.
   Then `python 5_estimation/mrqap_precision.py` (under a minute): the tests
   whose Monte Carlo interval contains 0.05, recomputed with 100,000 draws.
7. **Sensitivity.** `python 5_estimation/qv_sensitivity.py` (about half an
   hour), after step 6: the models under the four allocations of the exports
   declared without an importer.
8. **Positions and Fig. 3.** `python 5_estimation/layer_positions.py`, then
   `python 5_estimation/layer_network_figure.py`. Then
   `python 5_estimation/multiple_testing.py` (seconds), the second network under
   corrections for multiple testing, and
   `python 5_estimation/specification_sensitivity.py` (about ten minutes), the
   flow-weight tests under year effects and other level/change choices.
9. **Descriptive statistics.** `python 5_estimation/descriptive_statistics.py`,
    after steps 5 and 6 or on the packaged results.
10. **Synthetic design.** `python 6_synthetic/synthetic_experiments.py`,
    independent of the other steps.

Each step overwrites the packaged output of the same name; to compare, run in a
copy of the package.

## Data sources

| Source | Dataset or series | Selection | Stored in | Used for |
|---|---|---|---|---|
| Eurostat, Comext | DS-045409, EU trade since 1988 by HS2-4-6 and CN8 | annual, value in euro; exports of the EU27 reporters; imports of ten reporters | `data/comext_exports`, `data/comext_imports` | export networks; selection; declaration check |
| Eurostat | namq_10_a10, namq_10_a10_e | B1G CLV15_MEUR; EMP_DC THS_HW; NSA; NACE C; quarterly | `data/eurostat` | productivity attribute |
| Eurostat | nama_10_a64, nama_10_a64_e | B1G CLV15_MEUR; EMP_DC THS_HW; NACE C | `data/eurostat` | check of the productivity series |
| Eurostat | sts_inpp_a | producer prices, NACE C, PCH_SM | `data/eurostat` | deflator of the credit rate |
| Eurostat | nrg_pc_205 | band MWH2000-19999, X_VAT, EUR per kWh, both semesters | `data/eurostat` | electricity attribute |
| ECB, MFI interest rate statistics | MIR.M.&lt;country&gt;.B.A2Z.A.R.A.2240.&lt;currency&gt;.N | monthly, new business, non-financial corporations, revolving loans and overdrafts | `data/ecb_mir` | finance attribute |

The files were retrieved from the Eurostat and ECB APIs on 24 and 25 September
2026, with these requests:

- Comext: `https://ec.europa.eu/eurostat/api/comext/dissemination/statistics/1.0/data/DS-045409`,
  annual, value in euro, one reporter at a time, the 19 TCLF chapters;
- Eurostat datasets: `https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data/<dataset>`
  with the selections of the table;
- ECB: `https://data-api.ecb.europa.eu/service/data/MIR/M.<country>.B.A2Z.A.R.A.2240..N?startPeriod=2014-01&format=csvdata`,
  one request per member state.

Both sources revise their data, and a new retrieval can differ from the stored
files, which are the ones behind the results.

## Outputs and where they are used in the article

| File | Content | Article |
|---|---|---|
| `1_selection/selection_result.txt` | member states observed per chapter; the chapter and member-state trade-off; largest shares of exports declared without an importer and the gap of the 1% threshold | Section 4.2; Supplementary Section S5; Table S3 |
| `1_selection/window_check_result.txt` | the same rule over longer windows | Section 4.2 |
| `2_attributes/real_credit_cost.csv`, `real_credit_cost_flags.txt` | rate, producer-price change and gross real factor per member state and year | Section 4.3; Supplementary Section S6 |
| `2_attributes/manufacturing_productivity.csv`, `manufacturing_productivity_check.txt` | value added per hour worked per member state and year; completeness, flags, comparison with the annual accounts | Section 4.3; Supplementary Section S6 |
| `3_inputs/input_notes.txt` | zero cells per chapter; electricity and finance flags | Section 4; Supplementary Section S5; Table S3 |
| `3_inputs/check_weights.csv` | weight x_ij / X_i by the direct formula | check in estimation.do |
| `4_declaration_check/compare_declarations_result.txt` | exporter- against importer-declared weights, ten member states | Section 4.2; Table S2 |
| `5_estimation/results/unit_roots.csv` | Fisher-type Phillips-Perron tests | Section 4.4; Supplementary Section S7.1; Table S4 |
| `5_estimation/results/screen_models.csv` | the 306 models, corridor-clustered inference | Supplementary Data 1 |
| `5_estimation/results/mrqap.csv`, `mrqap_summary.txt` | MRQAP p values of the flow weight and the attribute edge values | Section 5; Table 4; Supplementary Data 1 |
| `5_estimation/results/mrqap_precision.csv`, `mrqap_precision.txt` | Monte Carlo intervals; the tests near 0.05 with 100,000 permutations | Section 5; Supplementary Data 1 |
| `5_estimation/results/qv_sensitivity.txt`, `qv_sensitivity_cells.csv` | the models under four allocations of the exports declared without an importer | Section 5; Section 4.7; Supplementary Section S8.1; Supplementary Data 2 |
| `5_estimation/results/layer_positions.txt`, `layer_pair_relations.csv` | relations between the before sets and between the after sets of the 153 pairs; the structurally equivalent pair; the positions | Section 5; Tables S6 and S7; Supplementary Data 3 |
| `5_estimation/results/fig_layer_network.pdf` | the second network | Fig. 3 |
| `5_estimation/results/multiple_testing.txt` | the second network under the Benjamini-Hochberg, Benjamini-Yekutieli and Holm corrections | Section 4.6; Supplementary Section S8.1 |
| `5_estimation/results/specification_sensitivity.txt` | the flow-weight tests with year effects and under other level/change choices of the attribute edge values | Supplementary Section S8.1 |
| `5_estimation/descriptive_statistics_result.txt` | shares of the EU27's TCLF exports; REST shares; the factor of equation (8); cell counts; producer prices in 2022 | Sections 4, 5 and 7; Table 4; Supplementary Sections S5-S8 |
| `6_synthetic/synthetic_results.json`, `figure1_boundary.pdf` | examples of Propositions 5-7, nested-boundary errors, fixed-subnet check | Supplementary Section S3; Fig. 2; Table S5; Supplementary Section S4 |

Supplementary Section S8.1 also states that the structurally equivalent pair is the
same under the p values from corridor-clustered standard errors: the rule of
`layer_positions.py` applied to the column `p_cluster` of `results/mrqap.csv`,
in place of the MRQAP p values, gives the same pair, 61-63.

In the result files `prod` is the productivity attribute as it enters the
models, that is its yearly change, as the unit-root step decides; `fin` and
`elec` enter in levels.

## Labels used in the code and the results

The scripts, the log and the result files use the labels in the left column. The right column gives the item of the article that each label denotes.

| Label in the package | Item in the article |
|---|---|
| section 4 (examples of Propositions 4-6) | Propositions 5-7; Section 3.4; Supplementary Section S3 |
| section 5; Figure 1; Table 3 | Fig. 2; Table S5; Section 4.1; Supplementary Section S4 |
| section 6; Appendix A | Section 4; Supplementary Sections S5-S8 |
| section 6.1; Tables A1, A2 | Sections 4.2, 5.3 and 5.4; Supplementary Section S5; Tables S2 and S3 |
| section 6.2 | Sections 4.3, 5.3 and 7; Supplementary Section S6 |
| section 6.3; Table A3 | Sections 4.4 and 4.6; Supplementary Section S7; Table S4 |
| section 6.4; Table 4; Figure 2 | Section 5; Table 4; Fig. 3; Supplementary Section S8 |
| Table 5 (layer_positions.py) | Table S6; Section 4.5 |
| section 6.5 | Section 5.3; Supplementary Section S8.3 |
| Supplementary Tables S1, S2, S3 | Supplementary Data 1, 2, 3 |
| screen; network weight; network of layers | the 306 models; flow weight; second network |
| partner; recorded; QV | importer or target; declared; exports declared without an importer |

## Reproducibility

The results in `5_estimation/results/` and `5_estimation/estimation.log` come
from runs of the package on 27 September 2026: `estimation.do` in Stata 17 and
the Python scripts with the versions listed above. `mrqap.py` recomputed the
306 models and found their coefficients, clustered standard errors and p values
equal to those of `results/screen_models.csv` (the largest differences are
below 4e-15). `qv_sensitivity.py` reproduced the MRQAP p values of
`results/mrqap.csv` exactly. In the log of the Stata run the local folders are removed from the paths of the
log file, of network_calc.ado and of a temporary file, and the input folder that
the log reads, 4_inputs, is numbered one higher than here (3_inputs). The files
read are the same, and nothing else in the log is changed. The scripts of steps 1-4, 9 and 10 were rerun on
a copy of the package, and every file they write that is packaged is
byte-identical to the packaged one. Step 10 also writes the PNG copy
`figure1_boundary.png`, which is not packaged. The figure files `fig_layer_network.pdf` and
`figure1_boundary.pdf` were redrawn on 6 October 2026 after a change of their
labels to the terms of the paper; no number changed.

## License and data reuse

The code in this package is provided under the same Academic and Research Use
License as the netcalc package (LICENSE). Eurostat data may be reused with
acknowledgement of the source (Commission Decision 2011/833/EU). ECB statistics
may be reused with the source quoted as "Source: ECB statistics".

## References

Talay, N. (2026). netcalc: directed edge weights from a panel of ordered node
pairs. Stata package, command network_calc version 2.0.0, commit 6012f3f.
https://github.com/aggilitas/stata-networks.

Talay, N., Acaroğlu, H., Günal, A. and García Márquez, F. P. (2026).
Algebraic invariant multilayer-network edge regression: multi-source data
fusion with macro-shock immunity. Knowledge-Based Systems, 352, 117007.
doi:10.1016/j.knosys.2026.117007.

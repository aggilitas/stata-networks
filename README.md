# Stata Networks Package

A Stata package for calculating network edge weights from a panel of ordered node pairs. Supports multiple network types (interaction, flow, attribute) and outputs panel-ready datasets for econometric analysis.

Version 2.1.0. The package is called `netcalc`, its one command is
`network_calc`, and `stata-networks` is the name of the repository in which
it is developed.

## Features

- **Three Network Types**: Interaction, Flow, and Attribute networks
- **Multi-subnet Support**: Feature-based and aggregate calculations for interaction and flow
- **Bidirectional Networks**: Outflow and inflow direction options
- **Automatic Frame Management**: Seamless data organization
- **Ready for Regression**: Compatible with ivreghdfe, reghdfe, and other panel estimators

## Network Types

### 1. Interaction Network (Multi-subnet required)
- **Formula**: inside a subnet, ω_ij^X = N_j^X / Σ_{k≠i} N_k^X, so the weights of a subnet sum to one over the targets of each source; the single-subnet copy is P_ij = Σ_X (N_i^X / N_i) · ω_ij^X, each subnet scaled by the ratio it holds at the source
- **Use Case**: Social network connections based on birthplace, ethnicity, etc.
- **Example**: Connection strength between Ankara residents born in Kars and Istanbul residents born in Kars

### 2. Flow Network (Single or Multi-subnet)
- **Formula**: w_ij = v_ij / Σ_{k≠i} v_ik, taken inside each subnet under `subnet(multi)`; the single-subnet copy scales each subnet by the ratio it holds at the node before adding them up
- **Use Case**: Migration flows, trade flows, capital flows
- **Values**: `source_value` is the quantity of the edge i,j as recorded at i, and `target_value` the quantity of the same edge as recorded at j, as with exports declared by the exporter and imports declared by the importer; where a single record exists, the same figure goes into both columns
- **Direction**: outflow, or inflow, which anchors the weight at the target: the weight of edge i,j is the value j records for it over the values j records for every edge entering it, w_ij = u_ij / Σ_{k≠j} u_kj with u read from `target_value`, the weight of i in what arrives at j

### 3. Attribute Network (Single-subnet)
- **Formula**: w_ij = ln(A_j / A_i) for outflow
- **Use Case**: Economic disparities (GDP, unemployment, education)
- **Direction**: outflow (target/source) or inflow (source/target)
- **Subnets**: none. An attribute describes the node, so `type(attribute)` takes `subnet(single)` only; levels recorded for groups within a node are reduced to the node before the call

## Installation

### Requirements
- Stata 16 or higher (for frame support)
- Optional: ivreghdfe, reghdfe (for regression analysis)

### Method 1: Net Install (Recommended)

Latest version:

```stata
net install netcalc, from("https://raw.githubusercontent.com/aggilitas/stata-networks/main/")
```

The package is named `netcalc`; the repository keeps its original name so
that the link printed in the article stays valid.

**If you installed a version before 2.0.0**, it was distributed under the
package name `stata-networks`. Remove it first, or both will sit in your
ado directory and shadow each other. `ado uninstall` takes the number
`ado dir` prints in brackets beside the package, not its name:

```stata
ado dir
ado uninstall [n]
```

**Note:** If you encounter SSL certificate errors, use Method 2.

### Method 1b: Install the Published Version (for replication)

To reproduce the results reported in the article, install the exact tagged
version used for it. This tag is fixed and is not affected by later changes
to the repository:

```stata
net install stata-networks, from("https://raw.githubusercontent.com/aggilitas/stata-networks/v1.0.0-kbs/")
```

The package name is `stata-networks` here, not `netcalc`: that tag predates
the rename and carries its own package descriptor.

Browse or download that version directly:

- Source: https://github.com/aggilitas/stata-networks/tree/v1.0.0-kbs
- ZIP: https://github.com/aggilitas/stata-networks/archive/refs/tags/v1.0.0-kbs.zip

### Method 2: Manual Installation

1. Download the latest version:
   https://github.com/aggilitas/stata-networks/archive/refs/heads/main.zip
   (or the published version: https://github.com/aggilitas/stata-networks/archive/refs/tags/v1.0.0-kbs.zip)
2. Extract to a folder
3. Add to Stata:

```stata
adopath + "C:/path/to/stata-networks/code"
```

## Usage

### Data Format

Single-subnet input:
```
year  source  target  source_value  target_value
```

Multi-subnet input:
```
year  feature  source  target  source_size  source_value
                               target_size  target_value
```

`size` is what the subnet weighs at that node (people born in a province
who live there, passengers carried by a mode), read as a ratio of the
subnet to the node; `value` is the quantity the network is about.

The data must be the complete panel of their rows: every period, every
ordered pair of distinct nodes and, with a feature, every level of the
feature, with one value for each node and a zero, which the data supply,
for a flow or an interaction that did not happen. The command fills in no
row and no value: data with a row missing are refused, and the missing
rows are listed. It also refuses a missing value, a self-loop, an edge
that appears twice in a period, and a source or target that is not a
string or holds an underscore.

The examples read the data files in `examples/` and run from that
directory. In the files split into subnets, `feature` holds the province
people were born in.

### Example 1: Interaction Network

```stata
import delimited test_interaction_multi.csv, clear
network_calc, type(interaction) subnet(multi) feature(feature) ///
    name(bplace)
```

### Example 2: Flow Network

```stata
import delimited test_flow_single.csv, clear
network_calc, type(flow) subnet(single) name(mig_out)
network_calc, type(flow) subnet(single) direction(inflow) name(mig_in)
```

### Example 3: Attribute Network

```stata
import delimited test_attribute_single.csv, clear
network_calc, type(attribute) subnet(single) name(sch)
```

### Example 4: Regression Analysis

The estimation lies outside `network_calc`, and so does the outcome: it
comes from a file of its own and is linked to the panel on its key.

```stata
frame create outcome
frame outcome: import delimited test_outcome.csv, clear varnames(1)
frame change networks_single
frlink 1:1 year source target, frame(outcome)
frget y, from(outcome)
egen pair = group(source target)
reghdfe y mig_out sch, absorb(pair year) vce(robust)
```

An attribute value is the difference of a target-period and a
source-period term, so source-period and target-period fixed effects
together would absorb `sch` entirely; the example absorbs the ordered pair
and the period instead.

The whole example, from the data to the estimation, is
`examples/example_session.do`; `examples/generate_test_data.do` builds its
data.

## Command Syntax

```stata
network_calc, type(interaction|flow|attribute) subnet(single|multi) name(network_name) [feature(varname)] [direction(outflow|inflow)] [debug]
```

**Parameters:**
- `type()`: Network type (required)
- `subnet()`: Single or multi-subnet (required)
- `name()`: Network name (required, valid Stata variable name; at most 25 characters with `subnet(multi)`, which adds `_fratio` to it for a second column)
- `feature()`: Feature variable (required for multi-subnet)
- `direction()`: Outflow or inflow (default: outflow)
- `debug`: Display detailed output

The values of `type()`, `subnet()` and `direction()` may be typed in any
case and shortened to an unambiguous leading part, as in `type(Flow)`,
`type(f)` or `direction(IN)`. `type(attribute)` takes `subnet(single)` only.

## Output Frames

The package creates two frames:

### networks_single
```
year  source  target  edge_id  network1  network2  ...
```

### networks_multi
```
year  feature  source  target  edge_id  network1_fratio  network1  ...
```

A multi-subnet call writes two columns into `networks_multi`: the network
and, beside it, the ratio of each subnet within the feature at its node.

Every network of a frame has the rows of the frame: the same periods and
edges and, in `networks_multi`, the same subnets. A call whose rows differ
from those of the frame is refused before anything is written, and the rows
on either side are listed; nothing is filled in. Every join is checked
against both frames before either is written, so a call writes both frames
or neither. Each call returns in `r()` the rows and edges it computed and
the mean of the variable.

## Project Structure

```
stata-networks/
├── code/
│   ├── network_calc.ado          # the command, the only public name
│   ├── network_calc.sthlp        # help file
│   ├── _netcalc_interaction.ado  # interaction template
│   ├── _netcalc_flow.ado         # flow template
│   ├── _netcalc_attribute.ado    # attribute template
│   ├── _netcalc_join.ado         # creates a frame or joins to it
│   └── _netcalc_aggregate.ado    # sums subnet weights (interaction, flow)
├── examples/
│   ├── example_session.do        # the session of the article, ending in an estimation
│   ├── example_session.log       # its log
│   ├── example_estimates.csv     # the estimates the session writes
│   ├── generate_test_data.do     # builds the data files below, with its log
│   ├── test_*.csv                 # the input files and the outcome
│   └── article_table2.csv        # the first row of each input file
├── tests/
│   ├── network_calc_cert.do      # certification script
│   └── network_calc_cert.log     # its log, run on Stata 17
├── netcalc.pkg                    # package descriptor
├── stata.toc                      # net install index
├── LICENSE                        # Academic and Research Use License
└── README.md
```

Names beginning with an underscore are internal routines. Only
`network_calc` is meant to be called.

## Citation

Citation is a condition of the [LICENSE](LICENSE). Any publication,
presentation, or academic work that uses this Software, **or results derived
from it**, must cite the article:

```
Talay, N., Acaroğlu, H., Günal, A., & García Márquez, F. P. (2026).
Algebraic Invariant Multilayer-Network Edge Regression: Multi-Source Data
Fusion with Macro-Shock Immunity. Knowledge-Based Systems, 352, 117007.
https://doi.org/10.1016/j.knosys.2026.117007
```

Optionally, you may additionally cite the software itself:

```
Talay, N. (2026). Stata Networks Package: Network Edge Calculator for
Econometric Analysis. GitHub repository:
https://github.com/aggilitas/stata-networks
```

## License

Academic and Research Use License - Free for academic and research purposes with mandatory citation. Commercial use requires a separate license. See [LICENSE](LICENSE) file for details. For commercial licensing inquiries: aggilitas@gmail.com

## Authors

**Necmi TALAY** (Maintainer)
- GitHub: [@aggilitas](https://github.com/aggilitas)

**Hakan ACAROĞLU**

**Aslıhan GÜNAL**

**Fausto Pedro GARCÍA MÁRQUEZ**

## Support

- Issues: https://github.com/aggilitas/stata-networks/issues
- Documentation: https://github.com/aggilitas/stata-networks

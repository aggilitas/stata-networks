# Stata Networks Package

A Stata package for calculating network edge weights from node-level data. Supports multiple network types (interaction, flow, attribute) and outputs panel-ready datasets for econometric analysis.

## Features

- **Three Network Types**: Interaction, Flow, and Attribute networks
- **Multi-subnet Support**: Feature-based and aggregate calculations
- **Bidirectional Networks**: Outflow and inflow direction options
- **Automatic Frame Management**: Seamless data organization
- **Ready for Regression**: Compatible with ivreghdfe, reghdfe, and other panel estimators

## Network Types

### 1. Interaction Network (Multiple-subnet required)
- **Formula**: e_ij^X = (N_i^X / N_i) · (n_j^X / Σ_{k≠i} N_k^X)
- **Use Case**: Social network connections based on birthplace, ethnicity, etc.
- **Example**: Connection strength between Ankara residents born in Kars and Istanbul residents born in Kars

### 2. Flow Network (Single or Multi-subnet)
- **Formula**: w_i = v_i / T(y,s)
- **Use Case**: Migration flows, trade flows, capital flows
- **Direction**: outflow (source_value) or inflow (target_value)

### 3. Attribute Network (Single or Multi-subnet)
- **Formula**: w_ij = ln(A_j / A_i) for outflow
- **Use Case**: Economic disparities (GDP, unemployment, education)
- **Direction**: outflow (target/source) or inflow (source/target)

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

### Example 1: Interaction Network

```stata
use "birthplace_data.dta", clear
network_calc, type(interaction) subnet(multi) feature(birthplace) ///
    name(bplace)
```

### Example 2: Flow Network

```stata
use "migration_data.dta", clear
network_calc, type(flow) subnet(single) name(mig_out)
network_calc, type(flow) subnet(single) direction(inflow) name(mig_in)
```

### Example 3: Attribute Network

```stata
use "schooling_data.dta", clear
network_calc, type(attribute) subnet(single) name(sch)
```

### Example 4: Regression Analysis

```stata
* Single-subnet regression
frame change networks_single
ivreghdfe y mig_out mig_in bplace sch, absorb(edge_id)

* Multi-subnet regression: bplace_fratio is the share the subnet takes
* at its node, which a multi-subnet call writes beside the weights
frame change networks_multi
ivreghdfe y bplace bplace_fratio, absorb(edge_id feature)
```

## Command Syntax

```stata
network_calc, type(interaction|flow|attribute) subnet(single|multi) name(network_name) [feature(varname)] [direction(outflow|inflow)] [debug]
```

**Parameters:**
- `type()`: Network type (required)
- `subnet()`: Single or multi-subnet (required)
- `name()`: Network name (required, valid Stata variable name)
- `feature()`: Feature variable (required for multi-subnet)
- `direction()`: Outflow or inflow (default: outflow)
- `debug`: Display detailed output

## Output Frames

The package creates two frames:

### networks_single
```
year  edge_id  network1  network2  network3  ...
```

### networks_multi
```
year  feature  edge_id  network1  network2  ...
```

## Project Structure

```
stata-networks/
├── code/
│   ├── network_calc.ado          # the command, the only public name
│   ├── network_calc.sthlp        # help file
│   ├── _netcalc_interaction.ado  # interaction template
│   ├── _netcalc_flow.ado         # flow template
│   ├── _netcalc_attribute.ado    # attribute template
│   ├── _netcalc_pool.ado         # combines raw data over the feature
│   ├── _netcalc_frames.ado       # frame subcommand dispatch
│   ├── _netcalc_join.ado         # creates a frame or joins to it
│   └── _netcalc_aggregate.ado    # sums subnet weights (interaction)
├── examples/                      # example datasets
├── tests/
│   └── network_calc_cert.do      # certification script
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
Algebraic Invariant Multilayer Network Edge Regression: Multi-Source Data
Fusion with Macro-Shock Immunity. Knowledge-Based Systems, 117007.
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

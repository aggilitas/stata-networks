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

```stata
net install stata-networks, from("https://aggilitas.github.io/stata-networks/")
```

**Note:** If you encounter SSL certificate errors, use Method 2.

### Method 2: Manual Installation

1. Download: https://github.com/aggilitas/stata-networks/archive/refs/heads/main.zip
2. Extract to a folder
3. Add to Stata:

```stata
adopath + "C:/path/to/stata-networks/code"
adopath + "C:/path/to/stata-networks/code/helpers"
```

## Usage

### Data Format

All network types require standardized input format:
```
year  [feature]  source  target  source_value  target_value
```

### Example 1: Interaction Network

```stata
use "birthplace_data.dta", clear
network_calc, type(interaction) subnet(multi) feature(birthplace) name(birth_place)
```

### Example 2: Flow Network

```stata
use "migration_data.dta", clear
network_calc, type(flow) subnet(single) direction(outflow) name(migration)
```

### Example 3: Attribute Network

```stata
use "attributes_data.dta", clear
network_calc, type(attribute) subnet(single) direction(outflow) name(gdp)
```

### Example 4: Regression Analysis

```stata
* Single-subnet regression
frame change networks_single
ivreghdfe migration birth_place gdp, absorb(edge_id)

* Multi-subnet regression
frame change networks_multi
ivreghdfe migration birth_place, absorb(edge_id feature)
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
│   ├── network_calc.ado          # Main command
│   └── helpers/
│       ├── calc_interaction.ado  # Interaction network calculations
│       ├── calc_flow.ado         # Flow network calculations
│       ├── calc_attribute.ado    # Attribute network calculations
│       └── frame_manager.ado     # Frame management
├── examples/                      # Example datasets
├── tests/                         # Test scripts
├── LICENSE                        # MIT License
└── README.md
```

## Citation

If you use this package in your research, please cite:

```
Talay, N., Acaroğlu, H., Günal, A., & García Márquez, F. P. (2026). 
Stata Networks Package: Network Edge Calculator for Econometric Analysis. 
GitHub repository: https://github.com/aggilitas/stata-networks
```

## License

MIT License - See [LICENSE](LICENSE) file for details.

## Authors

**Necmi TALAY** (Maintainer)
- GitHub: [@aggilitas](https://github.com/aggilitas)

**Hakan ACAROĞLU**

**Aslıhan GÜNAL**

**Fausto Pedro GARCÍA MÁRQUEZ**

## Support

- Issues: https://github.com/aggilitas/stata-networks/issues
- Documentation: https://github.com/aggilitas/stata-networks

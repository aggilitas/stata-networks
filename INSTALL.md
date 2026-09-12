# Installation Guide

## Method 1: Net Install (Recommended)

### Latest version

```stata
net install stata-networks, from("https://raw.githubusercontent.com/aggilitas/stata-networks/main/")
```

### Published version (for replication)

To reproduce the results reported in the article, install the exact tagged
version used for it. This tag is fixed and is not affected by later changes
to the repository:

```stata
net install stata-networks, from("https://raw.githubusercontent.com/aggilitas/stata-networks/v1.0.0-kbs/")
```

Browse or download that version directly:

- Source: https://github.com/aggilitas/stata-networks/tree/v1.0.0-kbs
- ZIP: https://github.com/aggilitas/stata-networks/archive/refs/tags/v1.0.0-kbs.zip

**Troubleshooting SSL Errors:**

If you encounter SSL certificate errors (common in Stata 17 and earlier):

```stata
set httpproxy off
net install stata-networks, from("https://raw.githubusercontent.com/aggilitas/stata-networks/main/")
```

If the error persists, use Method 2 (Manual Installation).

### Uninstall

```stata
ado uninstall stata-networks
```

---

## Method 2: Manual Installation

### Download and Extract

1. Download ZIP: https://github.com/aggilitas/stata-networks/archive/refs/heads/main.zip
   (published version: https://github.com/aggilitas/stata-networks/archive/refs/tags/v1.0.0-kbs.zip)
2. Extract to a folder (e.g., `C:/stata-packages/stata-networks/`)

### Add to Adopath

```stata
adopath + "C:/stata-packages/stata-networks/code"
adopath + "C:/stata-packages/stata-networks/code/helpers"
```

**Make it permanent** (add to profile.do):

```stata
doedit profile.do
```

Add these lines to profile.do:
```stata
adopath + "C:/stata-packages/stata-networks/code"
adopath + "C:/stata-packages/stata-networks/code/helpers"
```

---

## Method 3: Copy to ADO Directory

### Find your ADO directory

```stata
sysdir
```

Look for `PLUS` or `PERSONAL` directory.

### Copy files

Copy files to the appropriate subdirectories:

**Windows example:**
```
C:/Users/YourName/ado/plus/n/network_calc.ado
C:/Users/YourName/ado/plus/c/calc_interaction.ado
C:/Users/YourName/ado/plus/c/calc_flow.ado
C:/Users/YourName/ado/plus/c/calc_attribute.ado
C:/Users/YourName/ado/plus/f/frame_manager.ado
```

**Mac/Linux example:**
```
~/ado/plus/n/network_calc.ado
~/ado/plus/c/calc_interaction.ado
~/ado/plus/c/calc_flow.ado
~/ado/plus/c/calc_attribute.ado
~/ado/plus/f/frame_manager.ado
```

---

## Verify Installation

```stata
which network_calc
```

Should return the location of `network_calc.ado`

---

## Quick Start

```stata
* Load your data first (File > Open or use command)

* Calculate interaction network
network_calc, type(interaction) subnet(multi) feature(feature) name(birth_place)

* View results
frame change networks_single
describe
list in 1/10
```

---

## Requirements

- **Stata 16 or higher** (for frame support)
- **Optional:** ivreghdfe, reghdfe (for regression analysis)

---

## Support

- **Issues:** https://github.com/aggilitas/stata-networks/issues
- **Documentation:** https://github.com/aggilitas/stata-networks

---

## Authors

Necmi TALAY, Hakan ACAROĞLU, Aslıhan GÜNAL & Fausto Pedro GARCÍA MÁRQUEZ (2026)

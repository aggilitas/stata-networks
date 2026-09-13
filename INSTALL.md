# Installation Guide

## Method 1: Net Install (Recommended)

### Latest version

```stata
net install netcalc, from("https://raw.githubusercontent.com/aggilitas/stata-networks/main/")
```

The package is named `netcalc`. The repository keeps its original name so
that the link printed in the article stays valid; the name in the URL is
just a directory and does not affect the installed package.

**If you installed a version before 2.0.0**, it was distributed under the
package name `stata-networks`. Remove it first, or both will sit in your
ado directory and shadow each other. `ado uninstall` takes the number
`ado dir` prints in brackets beside the package, not its name:

```stata
ado dir
ado uninstall [n]
```

### Published version (for replication)

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

**Troubleshooting SSL Errors:**

If you encounter SSL certificate errors (common in Stata 17 and earlier):

```stata
set httpproxy off
net install netcalc, from("https://raw.githubusercontent.com/aggilitas/stata-networks/main/")
```

If the error persists, use Method 2 (Manual Installation).

### Uninstall

`ado uninstall` takes the number `ado dir` prints in brackets beside the
package, not its name:

```stata
ado dir
ado uninstall [n]
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
```

**Make it permanent** (add to profile.do):

```stata
doedit profile.do
```

Add this line to profile.do:
```stata
adopath + "C:/stata-packages/stata-networks/code"
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

Every file goes to the subdirectory named by its first character, and a
leading underscore counts as that character.

**Windows example:**
```
C:/Users/YourName/ado/plus/n/network_calc.ado
C:/Users/YourName/ado/plus/n/network_calc.sthlp
C:/Users/YourName/ado/plus/_/_netcalc_interaction.ado
C:/Users/YourName/ado/plus/_/_netcalc_flow.ado
C:/Users/YourName/ado/plus/_/_netcalc_attribute.ado
C:/Users/YourName/ado/plus/_/_netcalc_pool.ado
C:/Users/YourName/ado/plus/_/_netcalc_frames.ado
C:/Users/YourName/ado/plus/_/_netcalc_join.ado
C:/Users/YourName/ado/plus/_/_netcalc_aggregate.ado
```

**Mac/Linux example:** the same paths under `~/ado/plus/`.

---

## Verify Installation

```stata
which network_calc
help network_calc
```

The first returns the location of `network_calc.ado`, the second opens the
help file.

---

## Quick Start

```stata
* Load your data first
use birthplace.dta, clear

* Calculate interaction network
network_calc, type(interaction) subnet(multi) feature(birthplace) ///
    name(birth_place)

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

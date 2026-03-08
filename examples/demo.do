********************************************************************************
* STATA NETWORKS PACKAGE - DEMO SCRIPT
* Authors: Talay, Acaroğlu, Günal & García Márquez (2026)
* 
* This script demonstrates how to use the stata-networks package
* to calculate network edge weights and perform regression analysis.
*
* USAGE: Open your .dta file in Stata first, then run this script.
*        Or set your working directory with cd and use the use command.
********************************************************************************

clear all
set more off

********************************************************************************
* STEP 1: INSTALLATION
********************************************************************************

* Install the package (one-time setup)
* net install stata-networks, from("https://aggilitas.github.io/stata-networks/")

* Verify installation
which network_calc

********************************************************************************
* STEP 2: PREPARE YOUR DATA
********************************************************************************

* Your data should be in long format with the following structure:
*   Multi-subnet:  year  feature  source  target  source_value  target_value
*   Single-subnet: year  source  target  source_value  target_value

* For interaction networks:
*   feature    = subnet identifier (e.g., birth province)
*   source     = source node (e.g., province of residence)
*   target     = target node (e.g., destination province)
*   source_value = N_i^X (population born in X living in source)
*   target_value = N_j^X (population born in X living in target)

* Load your data (adjust path to your file)
* cd "C:/path/to/your/data"
* use "birthplace_data.dta", clear

********************************************************************************
* STEP 3: CALCULATE INTERACTION NETWORK (Multi-subnet)
********************************************************************************

* Interaction networks require a feature variable
* Formula: e_ij^X = (N_i^X / N_i) * (N_j^X / sum_{k!=i} N_k^X)

* Data must be loaded in memory before running:
network_calc, type(interaction) subnet(multi) feature(feature) name(birth_place)

********************************************************************************
* STEP 4: CALCULATE FLOW NETWORK
********************************************************************************

* Flow networks can be single or multi-subnet
* Formula: w_i = v_i / T(y,s)

* Single-subnet flow (load flow data first)
* network_calc, type(flow) subnet(single) direction(outflow) name(migration)

* Multi-subnet flow
* network_calc, type(flow) subnet(multi) feature(feature) direction(outflow) name(migration_bp)

********************************************************************************
* STEP 5: CALCULATE ATTRIBUTE NETWORK
********************************************************************************

* Attribute networks measure disparities between nodes
* Formula: w_ij = ln(A_j / A_i)

* Single-subnet attribute (load attribute data first)
* network_calc, type(attribute) subnet(single) direction(outflow) name(gdp)

********************************************************************************
* STEP 6: VIEW CALCULATED NETWORKS
********************************************************************************

* Single-subnet networks (all aggregated networks)
frame change networks_single
describe
list in 1/10
summarize

* Multi-subnet networks (feature-based networks)
frame change networks_multi
describe
list in 1/10

* Back to default frame
frame change default

********************************************************************************
* STEP 7: REGRESSION ANALYSIS
********************************************************************************

* Example: Single-subnet regression with edge fixed effects
frame change networks_single

* Basic OLS
* regress migration birth_place gdp unemployment

* With fixed effects (requires ivreghdfe)
* ivreghdfe migration birth_place gdp unemployment, absorb(edge_id)

********************************************************************************
* STEP 8: SAVE RESULTS
********************************************************************************

frame change networks_single
save "my_networks_single.dta", replace

frame change networks_multi
save "my_networks_multi.dta", replace

frame change default

********************************************************************************
* TIPS
********************************************************************************

* 1. Data format:
*    - Multi: year, feature, source, target, source_value, target_value
*    - Single: year, source, target, source_value, target_value

* 2. Network names must be valid Stata variable names

* 3. Direction option:
*    - outflow (default): uses source_value for flow, ln(target/source) for attribute
*    - inflow: uses target_value for flow, ln(source/target) for attribute

* 4. Use debug option for detailed output:
*    network_calc, type(interaction) subnet(multi) feature(feature) name(test) debug

********************************************************************************
di ""
di as result "Demo script completed!"
di as text "https://github.com/aggilitas/stata-networks"

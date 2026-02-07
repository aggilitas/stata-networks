********************************************************************************
* STATA NETWORKS PACKAGE - DEMO SCRIPT
* Authors: Talay, Acaroğlu, Günal & García Márquez (2026)
* 
* This script demonstrates how to use the stata-networks package
* to calculate network edge weights and perform regression analysis.
********************************************************************************

clear all
set more off

* Set working directory (adjust to your path)
* cd "C:/path/to/your/data"

********************************************************************************
* STEP 1: INSTALLATION
********************************************************************************

* Install the package (one-time setup)
* net install stata-networks, from("https://aggilitas.github.io/stata-networks/")

* OR add to adopath if installed manually
* adopath + "C:/path/to/stata-networks/code"
* adopath + "C:/path/to/stata-networks/code/helpers"

* Verify installation
which network_calc

********************************************************************************
* STEP 2: PREPARE YOUR DATA
********************************************************************************

* Your data should be in long format with the following structure:
* year  feature  source  target  source_value  target_value

* Example data structure:
* 2018  kars     ankara  istanbul  23000  45000
* 2018  kars     ankara  izmir     23000  12000
* 2018  adana    ankara  istanbul  15000  45000

* Load your data
* use "your_network_data.dta", clear

********************************************************************************
* STEP 3: CALCULATE INTERACTION NETWORK (Multi-subnet)
********************************************************************************

* Interaction networks require a feature variable (e.g., birthplace)
* Formula: e_ij^X = (N_i^X / N_i) * (n_j^X / sum_{k!=i} N_k^X)

* use "birthplace_data.dta", clear
* network_calc, type(interaction) subnet(multi) feature(birthplace) name(birth_place)

********************************************************************************
* STEP 4: CALCULATE FLOW NETWORK
********************************************************************************

* Flow networks can be single or multi-subnet
* Formula: w_i = v_i / T(y,s)

* Single-subnet flow (e.g., total migration)
* use "migration_data.dta", clear
* network_calc, type(flow) subnet(single) direction(outflow) name(migration)

* Multi-subnet flow (e.g., migration by birthplace)
* use "migration_data_feature.dta", clear
* network_calc, type(flow) subnet(multi) feature(birthplace) direction(outflow) name(migration_bp)

********************************************************************************
* STEP 5: CALCULATE ATTRIBUTE NETWORK
********************************************************************************

* Attribute networks measure disparities between nodes
* Formula: w_ij = ln(A_j / A_i)

* Single-subnet attribute (e.g., GDP disparities)
* use "attributes_data.dta", clear
* network_calc, type(attribute) subnet(single) direction(outflow) name(gdp)

* Additional attributes
* network_calc, type(attribute) subnet(single) direction(outflow) name(unemployment)
* network_calc, type(attribute) subnet(single) direction(outflow) name(education)

********************************************************************************
* STEP 6: VIEW CALCULATED NETWORKS
********************************************************************************

* Single-subnet networks (all aggregated networks)
frame change networks_single
describe
list in 1/10

* Summary statistics
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

* Example 1: Single-subnet regression with edge fixed effects
frame change networks_single

* Basic OLS
regress migration birth_place gdp unemployment

* With fixed effects (ivreghdfe)
ivreghdfe migration birth_place gdp unemployment, absorb(edge_id)

* With year and edge fixed effects
ivreghdfe migration birth_place gdp unemployment, absorb(edge_id year)

* Example 2: Multi-subnet regression with feature fixed effects
frame change networks_multi

* With edge and feature fixed effects
ivreghdfe migration birth_place, absorb(edge_id feature)

* With edge, feature, and year fixed effects
ivreghdfe migration birth_place, absorb(edge_id feature year)

********************************************************************************
* STEP 8: SAVE RESULTS
********************************************************************************

* Save calculated networks for later use
frame change networks_single
save "my_networks_single.dta", replace

frame change networks_multi
save "my_networks_multi.dta", replace

********************************************************************************
* STEP 9: RELOAD SAVED NETWORKS (Optional)
********************************************************************************

* If you want to use previously calculated networks:

* Clear frames
capture frame drop networks_single
capture frame drop networks_multi

* Create and load frames
frame create networks_single
frame networks_single: use "my_networks_single.dta"

frame create networks_multi
frame networks_multi: use "my_networks_multi.dta"

********************************************************************************
* ADDITIONAL TIPS
********************************************************************************

* 1. Always check your data format before running network_calc
*    Required columns depend on subnet type:
*    - Multi: year, feature, source, target, source_value, target_value
*    - Single: year, source, target, source_value, target_value

* 2. Network names must be valid Stata variable names (no spaces, special chars)

* 3. Direction option:
*    - outflow (default): uses source_value for flow, ln(target/source) for attribute
*    - inflow: uses target_value for flow, ln(source/target) for attribute

* 4. Feature variable is required for multi-subnet networks

* 5. All networks must have the same years and edges to be joined properly

* 6. Use debug option for detailed output during calculation:
*    network_calc, type(interaction) subnet(multi) feature(bp) name(test) debug

********************************************************************************
* END OF DEMO SCRIPT
********************************************************************************

di ""
di as result "Demo script completed!"
di as text "For more information, visit:"
di as text "  https://github.com/aggilitas/stata-networks"

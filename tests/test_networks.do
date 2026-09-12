********************************************************************************
* TEST SCRIPT FOR NETWORK_CALC COMMAND
* Date: 2026-02-07
* Purpose: Test all network calculation functions
********************************************************************************

clear all
set more off

* Set paths
global project_dir "/home/claude/networks-ado-project"
global code_dir "$project_dir/code"
global examples_dir "$project_dir/examples"

* Add helper directory to adopath
adopath + "$code_dir"
adopath + "$code_dir/helpers"

* Display adopath for debugging
di "Adopath:"
adopath

********************************************************************************
* TEST 1: INTERACTION NETWORK (Multi-subnet, required)
********************************************************************************

di ""
di as text "{hline 80}"
di as result "TEST 1: INTERACTION NETWORK (Multi-subnet)"
di as text "{hline 80}"

use "$examples_dir/test_interaction_multi.dta", clear
describe
list in 1/5

* Run network_calc
network_calc, type(interaction) ///
              subnet(multi) ///
              feature(feature) ///
              name(birth_place) ///
              debug

* Check results
di ""
di as text "Checking networks_multi frame..."
frame change networks_multi
describe
list in 1/10

di ""
di as text "Checking networks_single frame (aggregated)..."
frame change networks_single
describe
list in 1/10

* Reset to default frame
frame change default

********************************************************************************
* TEST 2: FLOW NETWORK (Multi-subnet)
********************************************************************************

di ""
di as text "{hline 80}"
di as result "TEST 2: FLOW NETWORK (Multi-subnet)"
di as text "{hline 80}"

use "$examples_dir/test_flow_multi.dta", clear
describe
list in 1/5

* Run network_calc
network_calc, type(flow) ///
              subnet(multi) ///
              feature(feature) ///
              direction(outflow) ///
              name(migration) ///
              debug

* Check results
frame change networks_multi
describe
list in 1/10

frame change networks_single
describe
list in 1/10

frame change default

********************************************************************************
* TEST 3: FLOW NETWORK (Single-subnet)
********************************************************************************

di ""
di as text "{hline 80}"
di as result "TEST 3: FLOW NETWORK (Single-subnet)"
di as text "{hline 80}"

use "$examples_dir/test_flow_single.dta", clear
describe
list in 1/5

* Run network_calc
network_calc, type(flow) ///
              subnet(single) ///
              direction(outflow) ///
              name(total_migration) ///
              debug

* Check results
frame change networks_single
describe
list in 1/10

frame change default

********************************************************************************
* TEST 4: ATTRIBUTE NETWORK (Single-subnet)
********************************************************************************

di ""
di as text "{hline 80}"
di as result "TEST 4: ATTRIBUTE NETWORK (Single-subnet)"
di as text "{hline 80}"

use "$examples_dir/test_attribute_single.dta", clear
describe
list in 1/5

* Run network_calc
network_calc, type(attribute) ///
              subnet(single) ///
              direction(outflow) ///
              name(gdp) ///
              debug

* Check results
frame change networks_single
describe
summarize gdp, detail
list in 1/10

frame change default

********************************************************************************
* TEST 5: ATTRIBUTE NETWORK (Multi-subnet)
********************************************************************************

di ""
di as text "{hline 80}"
di as result "TEST 5: ATTRIBUTE NETWORK (Multi-subnet)"
di as text "{hline 80}"

use "$examples_dir/test_attribute_multi.dta", clear
describe
list in 1/5

* Run network_calc
network_calc, type(attribute) ///
              subnet(multi) ///
              feature(feature) ///
              direction(outflow) ///
              name(gdp_sector) ///
              debug

* Check results
frame change networks_multi
describe
list in 1/10

frame change networks_single
describe
list in 1/10

frame change default

********************************************************************************
* FINAL SUMMARY
********************************************************************************

di ""
di as text "{hline 80}"
di as result "FINAL SUMMARY: ALL FRAMES"
di as text "{hline 80}"

di ""
di as text "Frame: networks_single"
frame networks_single {
    describe
    di ""
    di as text "Variables in networks_single:"
    describe, simple
    di ""
    di as text "Sample data:"
    list in 1/5, clean
}

di ""
di as text "Frame: networks_multi"
frame networks_multi {
    describe
    di ""
    di as text "Variables in networks_multi:"
    describe, simple
    di ""
    di as text "Sample data:"
    list in 1/5, clean
}

di ""
di as text "{hline 80}"
di as result "ALL TESTS COMPLETED SUCCESSFULLY!"
di as text "{hline 80}"

* Save frames for inspection
di ""
di as text "Saving frames to disk..."
frame networks_single: save "$examples_dir/output_networks_single.dta", replace
frame networks_multi: save "$examples_dir/output_networks_multi.dta", replace
di as text "Saved to:"
di as text "  - $examples_dir/output_networks_single.dta"
di as text "  - $examples_dir/output_networks_multi.dta"

di ""
di as text "Test script completed!"

*! generate_test_data.do
*! Builds the example datasets of netcalc 2.1.0 and writes them beside
*! this file. Run it from the examples directory.
*!
*! Layout, multi-subnet:
*!     year feature source target source_size source_value
*!                                target_size target_value
*! Layout, single-subnet:
*!     year source target source_value target_value
*!
*! What the columns hold:
*!   test_interaction_multi.csv
*!       size   people of the birthplace group living at the node
*!       value  those of them in employment
*!   test_flow_multi.csv
*!       size   people of the birthplace group living at the node
*!       value  migrants of the group along the edge: source_value as
*!              the sending node records them, target_value the same
*!              flow as the receiving node records it
*!   test_flow_single.csv
*!       the subnet flows added up over the feature, both records
*!   test_attribute_single.csv
*!       years of schooling at the node: the population-weighted
*!       mean of the schooling of the birthplace groups living there
*!   test_outcome.csv
*!       a synthetic outcome y on the edge, built with known
*!       coefficients: 2 on the single-subnet copy of the flow network
*!       and 0.5 on the schooling log-ratio
*!
*! Size and value differ in every multi-subnet file, so the
*! single-subnet copy of the flow network, which weighs each subnet by
*! its population at the node, differs from the flow network computed
*! from the pooled file.

*!
*! Outputs, all written to the working directory and checked at the
*! end of the run: the five files above, article_table2.csv (the first
*! row of each file the example session reads, table 2 of the
*! article), and this run's log, generate_test_data.log.

version 16.0
clear all
capture log close
log using generate_test_data.log, text replace
set seed 20260912

*--------------------------------------------------------------
* Five provinces, which are both the nodes and the birthplace
* groups
*--------------------------------------------------------------

input str4 node byte norder
"van"  1
"kars" 2
"bolu" 3
"rize" 4
"ordu" 5
end
tempfile nodes
save `nodes'

*--------------------------------------------------------------
* Node level: one row per year, birthplace group, and node
*--------------------------------------------------------------

rename (node norder) (feature forder)
cross using `nodes'
expand 3
bysort forder norder: generate int year = 2017 + _n
sort year forder norder

* people of the group at the node; the group is largest at home
generate long size = cond(feature == node, 40000, ///
                          runiformint(1500, 45000))
replace size = size + (year - 2018) * runiformint(50, 900)

* years of schooling of the group at the node
generate double schooling = round(runiform(5, 13), .01)

* those of the group in employment
generate long employed = round(size * runiform(.35, .75))

tempfile nodelevel
save `nodelevel'

*--------------------------------------------------------------
* Edge level: one row per year, birthplace group, and ordered
* pair of distinct nodes
*--------------------------------------------------------------

rename (node norder size employed schooling) ///
       (source sorder source_size source_employed source_schooling)
tempfile src
save `src'

use `nodelevel', clear
rename (node norder size employed schooling) ///
       (target torder target_size target_employed target_schooling)
joinby year feature forder using `src'
drop if source == target
sort year forder sorder torder

* migrants of the group along the edge as the sending node records
* them, and the same flow as the receiving node records it
generate long flow = runiformint(20, 3000)
generate long flow_at_target = round(flow * runiform(.9, 1.1))

tempfile edges
save `edges'

local multi year feature source target ///
            source_size source_value target_size target_value

*--------------------------------------------------------------
* Interaction: subnets weighed by population, the weight
* distributing employment
*--------------------------------------------------------------

use `edges', clear
rename (source_employed target_employed) (source_value target_value)
keep `multi'
order `multi'
export delimited using test_interaction_multi.csv, replace

*--------------------------------------------------------------
* Flow: subnets weighed by population, the weight distributing
* migrants; two records of the same flow
*--------------------------------------------------------------

use `edges', clear
rename (flow flow_at_target) (source_value target_value)
keep `multi'
order `multi'
export delimited using test_flow_multi.csv, replace

* the same flows added up over the feature
use `edges', clear
collapse (sum) source_value = flow target_value = flow_at_target, ///
    by(year sorder torder source target)
sort year sorder torder
keep year source target source_value target_value
format source_value target_value %9.0f
export delimited using test_flow_single.csv, replace datafmt

*--------------------------------------------------------------
* Attribute: years of schooling at the node. An attribute
* describes the node and has no subnets, so the levels of the
* groups are reduced to the node first, weighted by population.
*--------------------------------------------------------------

use `nodelevel', clear
generate double weighted = size * schooling
collapse (sum) weighted size, by(year node norder)
generate double level = round(weighted / size, .0001)
keep year node norder level
tempfile level
save `level'

rename (node norder level) (source sorder source_value)
tempfile slevel
save `slevel'
use `level', clear
rename (node norder level) (target torder target_value)
joinby year using `slevel'
drop if source == target
sort year sorder torder
keep year source target source_value target_value
format source_value target_value %7.4f
export delimited using test_attribute_single.csv, replace datafmt

*--------------------------------------------------------------
* Outcome: known coefficients, 2 on the single-subnet copy of the
* flow network and 0.5 on the schooling log-ratio
*--------------------------------------------------------------

* population of each node, over all groups
use `nodelevel', clear
collapse (sum) pop = size, by(year node)
rename node source
tempfile pop
save `pop'

* the copy adds up the subnet weights, each scaled by the
* population ratio of its group at the source
use `edges', clear
merge m:1 year source using `pop', nogenerate assert(match)
bysort year forder sorder: egen double sent = total(flow)
generate double part = source_size / pop * flow / sent
collapse (sum) copy = part, by(year sorder torder source target)

* the schooling log-ratio, from the node levels written above
rename source node
merge m:1 year node using `level', keepusing(level) ///
    nogenerate assert(match)
rename (node level) (source source_level)
rename target node
merge m:1 year node using `level', keepusing(level) ///
    nogenerate assert(match)
rename (node level) (target target_level)
generate double sch = ln(target_level / source_level)

sort year sorder torder
generate double y = 1 + 2 * copy + .5 * sch + rnormal(0, .05)
keep year source target y
format y %9.6f
export delimited using test_outcome.csv, replace datafmt

*--------------------------------------------------------------
* Table 2 of the article: the first row of each file the example
* session reads, one row per file
*--------------------------------------------------------------

tempfile t2
local k = 0
foreach f in interaction_multi flow_multi flow_single attribute_single {
    import delimited test_`f'.csv, clear varnames(1) stringcols(_all)
    keep in 1
    generate str32 file = "test_`f'"
    generate byte order = `++k'
    if `k' > 1 {
        append using `t2'
    }
    save `t2', replace
}
use `t2', clear
sort order
foreach v in feature source_size target_size {
    capture confirm variable `v'
    if _rc {
        generate str1 `v' = ""
    }
}
order file year feature source target source_size source_value ///
      target_size target_value
keep file year feature source target source_size source_value ///
     target_size target_value
list, noobs abbreviate(16)
export delimited using article_table2.csv, replace

*--------------------------------------------------------------
* What this run wrote
*--------------------------------------------------------------

display as text _n "Files written to `c(pwd)':"
foreach f in test_interaction_multi.csv test_flow_multi.csv ///
             test_flow_single.csv test_attribute_single.csv ///
             test_outcome.csv article_table2.csv {
    confirm file `f'
    display as text "  `f'"
}
display as text "  generate_test_data.log"

log close

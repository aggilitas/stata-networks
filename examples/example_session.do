*! netcalc example session
*! Run from the examples directory of the repository, after
*! generate_test_data.do has built the input files there. Each call
*! computes one network and adds it to the edge panel, so the calls
*! together build a multi-network panel, and the session ends with an
*! estimation on that panel, with three standard errors for the same
*! coefficients. The estimation needs reghdfe and ftools.
*!
*! Outputs, written to the working directory and checked at the end
*! of the run: example_session.log, the log the article quotes, and
*! example_estimates.csv, the coefficients, the three standard errors,
*! the number of observations and the R-squared of the estimation in
*! section 6.5.

version 16.0
clear all

* the listings below are laid out to this width, which is what the
* Stata Journal asks of code and output alike
set linesize 79

* the input files are built where they are used
foreach f in interaction_multi flow_multi flow_single ///
             attribute_single outcome {
    capture confirm file test_`f'.csv
    if _rc {
        display as error "test_`f'.csv is not here: run" ///
                         " generate_test_data.do first"
        exit 601
    }
}

* the session writes itself beside this file
capture log close
log using example_session.log, text replace

*--------------------------------------------------------------
* The input: a long panel of ordered node pairs split into subnets
*
* 81 nodes over six years, 2018 to 2023, and the people grouped by
* the node they were born in, so the feature has the 81 levels of
* the nodes. size gives the subnet its ratio at the node and value
* is the quantity being measured; the two differ in every
* multi-subnet file.
*--------------------------------------------------------------

foreach f in interaction_multi flow_multi flow_single attribute_single {
    import delimited test_`f'.csv, clear varnames(1) rowrange(1:2)
    display as text _n "test_`f'.csv"
    list in 1, noobs abbreviate(16)
}

*--------------------------------------------------------------
* An interaction network
*
* How the employed members of a birthplace group outside the
* source are distributed over the targets. A subnet is a network of
* its own, so its weights add up to one; the subnets are weighed
* by population when they are put back together.
*--------------------------------------------------------------

import delimited test_interaction_multi.csv, clear varnames(1)
network_calc, type(interaction) subnet(multi) feature(feature) ///
    name(bplace)
return list

*--------------------------------------------------------------
* A flow network over the same subnets
*
* The weight of the edge in the migrants the subnet sends from its
* node, as the sending node records them. Both frames are written:
* the subnet weights, and beside them the population ratio of each
* subnet, which the single-subnet copy uses.
*--------------------------------------------------------------

import delimited test_flow_multi.csv, clear varnames(1)
network_calc, type(flow) subnet(multi) feature(feature) ///
    name(mig_out)

*--------------------------------------------------------------
* The inflow network
*
* The weight of the source in the migrants that arrive at the
* target, as the receiving node records them.
*--------------------------------------------------------------

import delimited test_flow_multi.csv, clear varnames(1)
network_calc, type(flow) subnet(multi) feature(feature) ///
    direction(inflow) name(mig_in)

*--------------------------------------------------------------
* A single-subnet attribute network
*
* The log ratio of the two node values. Passed at the node level,
* so subnet(single) and no feature.
*--------------------------------------------------------------

import delimited test_attribute_single.csv, clear varnames(1)
network_calc, type(attribute) subnet(single) name(sch)

*--------------------------------------------------------------
* The flow network computed from the pooled file
*
* Since size and value differ, it is not the single-subnet copy of
* mig_out: the copy weighs each subnet by its population, the
* pooled network by the migrants it sends.
*--------------------------------------------------------------

import delimited test_flow_single.csv, clear varnames(1)
network_calc, type(flow) subnet(single) name(mig_pool)

*--------------------------------------------------------------
* The panel the calls have built
*--------------------------------------------------------------

frame change networks_single
describe, short
format bplace mig_out mig_in sch mig_pool %8.4f
list year source target bplace mig_out mig_in sch in 1/8, ///
    noobs abbreviate(16)

* the weights leaving a node add up to one in every year, less the
* ratios of the subnets whose total is zero (section 4.1 of the
* article): 486 node-years
preserve
    collapse (sum) mig_out, by(year source)
    summarize mig_out
restore

* the inflow weights entering a node add up to one in every year
preserve
    collapse (sum) mig_in, by(year target)
    summarize mig_in
restore

* an attribute edge value is a log ratio, so it cancels along the
* reversed edge
preserve
    generate str24 pair = cond(source < target, ///
                               source + "|" + target, ///
                               target + "|" + source)
    collapse (sum) sch, by(year pair)
    summarize sch
restore

* the single-subnet copy and the pooled network differ
generate double gap = abs(mig_out - mig_pool)
summarize gap
drop gap

*--------------------------------------------------------------
* The subnet weights themselves, in the multi-subnet frame
*--------------------------------------------------------------

frame change networks_multi
describe, short
format bplace_fratio bplace %7.4f
format mig_out_fratio mig_out %7.4f
format mig_in_fratio mig_in %7.4f
* every network in the frame, and beside each the ratio its subnet
* takes at the node
list year feature source target bplace_fratio bplace ///
    mig_out_fratio mig_out in 1/9, noobs abbreviate(16)

* a subnet is a network of its own, so its weights add up to one:
* the first five subnets of p01 in 2018, and all 39,366 subnet
* node-years
preserve
    collapse (sum) mig_out, by(year feature source)
    format mig_out %8.4f
    list if year == 2018 & source == "p01" & feature <= "p05", ///
        noobs abbreviate(16)
    summarize mig_out
restore

* and the ratios those subnets hold at the node add up to one
preserve
    bysort year feature source: keep if _n == 1
    collapse (sum) mig_out_fratio, by(year source)
    summarize mig_out_fratio
restore

*--------------------------------------------------------------
* An estimation on the panel
*
* The outcome comes from a file of its own, on the same key as the
* panel. It was generated as 2 times the single-subnet copy of the
* flow network, mig_out, plus 0.5 times the schooling log-ratio, sch,
* plus an effect of the ordered pair, an effect of the period, and a
* disturbance with a part common to the edges leaving a node in a
* period and a part common to the edges entering one. The ordered
* pair and the period are absorbed: source-period and target-period
* effects together would absorb sch entirely, since a log-ratio is
* the difference of a target-period and a source-period term.
*
* The same coefficients are reported with three standard errors.
* Heteroskedasticity-robust errors treat the edges as independent,
* which edges sharing a node are not. Two-way clustering on source
* and target allows the dependence among the edges that share either
* node. The node jackknife leaves one node out at a time, every edge
* it touches with it, and combines the 81 sets of coefficients with
* the multiplier of Cameron and Miller (2014, eq. 2.17).
*
* The ordered pairs are numbered for the edge effects. The nodes are
* numbered with one value label, so that a node has the same number
* as source and as target.
*--------------------------------------------------------------

frame create outcome
frame outcome: import delimited test_outcome.csv, clear varnames(1)
frame change networks_single
frlink 1:1 year source target, frame(outcome)
frget y, from(outcome)
egen pair = group(source target)
encode source, generate(src) label(node)
encode target, generate(tgt) label(node)

reghdfe y mig_out sch, absorb(pair year) vce(robust)
matrix b = e(b)
local n_obs = e(N)
local r2 = e(r2)
local se_r_mig = _se[mig_out]
local se_r_sch = _se[sch]

reghdfe y mig_out sch, absorb(pair year) vce(cluster src tgt)
local se_c_mig = _se[mig_out]
local se_c_sch = _se[sch]

* the node jackknife: the coefficients without each node in turn,
* combined as in Cameron and Miller (2014, eq. 2.17), whose multiplier
* of the sum of squared deviations is (G - 2) / (2 G) for G nodes;
* r(Var) is that sum divided by G - 1
frame create jack int node double(b_mig b_sch)
forvalues k = 1/81 {
    quietly reghdfe y mig_out sch if src != `k' & tgt != `k', ///
        absorb(pair year)
    frame post jack (`k') (_b[mig_out]) (_b[sch])
}
frame jack {
    quietly summarize b_mig
    local se_j_mig = sqrt((r(N) - 2) / (2 * r(N)) * (r(N) - 1) * r(Var))
    quietly summarize b_sch
    local se_j_sch = sqrt((r(N) - 2) / (2 * r(N)) * (r(N) - 1) * r(Var))
}

* the coefficients and the three standard errors side by side
frame create estimates str16 term double(estimate se_robust ///
    se_twoway se_jackknife)
frame post estimates ("mig_out") (b[1, 1]) (`se_r_mig') ///
    (`se_c_mig') (`se_j_mig')
frame post estimates ("sch") (b[1, 2]) (`se_r_sch') ///
    (`se_c_sch') (`se_j_sch')
frame post estimates ("N") (`n_obs') (.) (.) (.)
frame post estimates ("r2") (`r2') (.) (.) (.)
frame estimates {
    format estimate se_robust se_twoway se_jackknife %9.4f
    list if inlist(term, "mig_out", "sch"), noobs abbreviate(16)
    export delimited using example_estimates.csv, replace
}
display as text "N = " as result `n_obs' as text ///
    ", R-squared = " as result %6.4f `r2'

*--------------------------------------------------------------
* What one call replaces: the interaction network bplace built
* with built-in commands, each taking a total over its own group
*--------------------------------------------------------------

frame create byhand
frame byhand {
    import delimited test_interaction_multi.csv, clear varnames(1)
    * the subnet at the target over the subnet at every node but the
    * source: on the mesh, the rows of a source are its alternatives
    bysort year feature source: egen double outside = total(target_value)
    generate double omega = cond(outside == 0, 0, target_value / outside)
    * the ratio of the subnet at the source, its size read once
    bysort year source feature: generate byte first = _n == 1
    bysort year source: egen double node = total(source_size * first)
    generate double p = source_size / node
    * the subnets put back together
    generate double part = p * omega
    collapse (sum) bplace_hand = part, by(year source target)
}
frlink 1:1 year source target, frame(byhand)
frget bplace_hand, from(byhand)
assert reldif(bplace, bplace_hand) < 1e-12
drop byhand bplace_hand

frame change default

*--------------------------------------------------------------
* What this run wrote
*--------------------------------------------------------------

confirm file example_estimates.csv
display as text _n "Files written to `c(pwd)':"
display as text "  example_session.log"
display as text "  example_estimates.csv"

log close

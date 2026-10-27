*! netcalc example session
*! Run from the examples directory of the repository, where the input
*! files are; generate_test_data.do builds them. Each call computes
*! one network and adds it to the edge panel, so the calls together
*! build a multi-network panel, and the session ends with an
*! estimation on that panel. The estimation needs reghdfe and ftools.
*!
*! Outputs, written to the working directory and checked at the end
*! of the run: example_session.log, the log the article quotes, and
*! example_estimates.csv, the coefficients, standard errors, number
*! of observations and R-squared of the estimation in section 6.5.

version 16.0
clear all

* the listings below are laid out to this width, which is what the
* Stata Journal asks of code and output alike
set linesize 79

* the session writes itself beside this file
capture log close
log using example_session.log, text replace

*--------------------------------------------------------------
* The input: a long panel of ordered node pairs split into subnets
*
* Five provinces, three years, and the people grouped by the
* province they were born in. size gives the subnet its ratio at
* the node and value is the quantity being measured; the two
* differ in every multi-subnet file.
*--------------------------------------------------------------

foreach f in interaction_multi flow_multi flow_single attribute_single {
    import delimited test_`f'.csv, clear varnames(1)
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
format bplace mig_out mig_in sch mig_pool %8.4f
list year source target bplace mig_out mig_in sch in 1/8, ///
    noobs abbreviate(16)

* the weights leaving a node add up to one in every year
preserve
    collapse (sum) mig_out, by(year source)
    format mig_out %8.4f
    list, noobs abbreviate(16)
restore

* the inflow weights entering a node add up to one in every year
preserve
    collapse (sum) mig_in, by(year target)
    format mig_in %8.4f
    list, noobs abbreviate(16)
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
format bplace_fratio bplace %7.4f
format mig_out_fratio mig_out %7.4f
format mig_in_fratio mig_in %7.4f
* every network in the frame, and beside each the ratio its subnet
* takes at the node
list year feature source target bplace_fratio bplace ///
    mig_out_fratio mig_out in 1/9, noobs abbreviate(16)

* a subnet is a network of its own, so its weights add up to one
preserve
    collapse (sum) mig_out, by(year feature source)
    format mig_out %8.4f
    list if year == 2018 & source == "van", noobs abbreviate(16)
restore

* and the ratios those subnets hold at the node add up to one
preserve
    bysort year feature source: keep if _n == 1
    collapse (sum) mig_out_fratio, by(year source)
    format mig_out_fratio %8.4f
    list, noobs abbreviate(16)
restore

*--------------------------------------------------------------
* An estimation on the panel
*
* The outcome comes from a file of its own, on the same key as the
* panel. It was generated with known coefficients: 2 on the
* single-subnet copy of the flow network, mig_out, and 0.5 on the
* schooling log-ratio, sch. The ordered pair and the period are
* absorbed: source-period and target-period effects together would
* absorb sch entirely, since a log-ratio is the difference of a
* target-period and a source-period term. With five nodes no
* cluster-robust variance is reliable, so the standard errors are
* robust to heteroskedasticity only.
*--------------------------------------------------------------

frame create outcome
frame outcome: import delimited test_outcome.csv, clear varnames(1)
frame change networks_single
frlink 1:1 year source target, frame(outcome)
frget y, from(outcome)
egen pair = group(source target)
reghdfe y mig_out sch, absorb(pair year) vce(robust)

* the estimates, written for the article
frame create estimates str16 term double(estimate se)
foreach t in mig_out sch {
    frame post estimates ("`t'") (_b[`t']) (_se[`t'])
}
frame post estimates ("N") (e(N)) (.)
frame post estimates ("r2") (e(r2)) (.)
frame estimates: list, noobs abbreviate(16)
frame estimates: export delimited using example_estimates.csv, replace

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
    generate double omega = target_value / outside
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

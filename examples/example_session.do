*! netcalc example session
*! Run from the examples directory of the repository, where the input
*! files are. Each call computes one network and adds it to the edge
*! panel, so the calls together build a multi-network panel.

clear all

*--------------------------------------------------------------
* The input: a long node-level panel split into subnets
*
* Five provinces, three years, and the migrants grouped by the
* province they were born in. size is what the subnet weighs at
* the node and value is the quantity being measured.
*--------------------------------------------------------------

import delimited test_interaction_multi.csv, clear varnames(1)
describe
list in 1/6, noobs abbreviate(12)

*--------------------------------------------------------------
* An interaction network
*
* The share of the subnet at the source node times the share of
* the target node in what that subnet holds elsewhere. It has no
* single-subnet form, so subnet(multi) is required.
*--------------------------------------------------------------

network_calc, type(interaction) subnet(multi) feature(feature) ///
    name(int_bp)

*--------------------------------------------------------------
* A flow network over the same subnets
*
* The share of the edge in what leaves its node, scaled by the
* share of the subnet itself. Both frames are written: the subnet
* weights and their sum.
*--------------------------------------------------------------

import delimited test_flow_multi.csv, clear varnames(1)
network_calc, type(flow) subnet(multi) feature(feature) ///
    name(mig_bp)

*--------------------------------------------------------------
* The same flow network read from the other end of the edge
*--------------------------------------------------------------

import delimited test_flow_multi.csv, clear varnames(1)
network_calc, type(flow) subnet(multi) feature(feature) ///
    direction(inflow) name(mig_bp_in)

*--------------------------------------------------------------
* A single-subnet attribute network
*
* The log ratio of the two node values. Passed at the node level,
* so subnet(single) and no feature.
*--------------------------------------------------------------

import delimited test_attribute_single.csv, clear varnames(1)
list in 1/6, noobs abbreviate(12)

network_calc, type(attribute) subnet(single) name(sch)

*--------------------------------------------------------------
* The panel the four calls have built
*--------------------------------------------------------------

frame change networks_single
describe
list in 1/8, noobs abbreviate(12)

* a flow weight is a share, so the weights leaving a node add up
* to one in every year
preserve
    split edge_id, parse("_") gen(nd)
    collapse (sum) mig_bp, by(year nd1)
    list, noobs
restore

* an attribute weight is a log ratio, so it cancels along the
* reversed edge
preserve
    split edge_id, parse("_") gen(nd)
    generate str24 pair = cond(nd1 < nd2, nd1 + "|" + nd2, ///
                                          nd2 + "|" + nd1)
    collapse (sum) sch, by(year pair)
    summarize sch
restore

*--------------------------------------------------------------
* The subnet weights themselves, in the multi-subnet frame
*--------------------------------------------------------------

frame change networks_multi
describe
list in 1/9, noobs abbreviate(12)

* within one subnet the weights add up to the share of that
* subnet, and only the subnets together add up to one
preserve
    split edge_id, parse("_") gen(nd)
    collapse (sum) mig_bp, by(year feature nd1)
    list if year == 2018 & nd1 == "ankara", noobs
restore

frame change default

*! netcalc example session
*! Run from the examples directory of the repository, where the input
*! files are. Each call computes one network and adds it to the edge
*! panel, so the calls together build a multi-network panel.

clear all

*--------------------------------------------------------------
* The input: a long node-level panel split into subnets
*
* Five provinces, three years, and the migrants grouped by the
* province they were born in. size gives the subnet its ratio and
* value is the quantity being measured.
*--------------------------------------------------------------

import delimited test_interaction_multi.csv, clear varnames(1)
describe
format feature source target %4s
format source_size source_value target_size target_value %8.0g
list in 1/6, noobs abbreviate(16)

*--------------------------------------------------------------
* An interaction network
*
* The share of the subnet at the source node times the share of
* the target node in what that subnet holds elsewhere. It has no
* single-subnet form, so subnet(multi) is required.
*--------------------------------------------------------------

network_calc, type(interaction) subnet(multi) feature(feature) ///
    name(bplace)

*--------------------------------------------------------------
* A flow network over the same subnets
*
* The share of the edge in what leaves its node, scaled by the
* share of the subnet itself. Both frames are written: the subnet
* weights and their sum.
*--------------------------------------------------------------

import delimited test_flow_multi.csv, clear varnames(1)
network_calc, type(flow) subnet(multi) feature(feature) ///
    name(mig_out)

*--------------------------------------------------------------
* The same flow network read from the other end of the edge
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
format source target %4s
format source_value target_value %8.4f
list in 1/6, noobs abbreviate(16)

network_calc, type(attribute) subnet(single) name(sch)

*--------------------------------------------------------------
* The panel the four calls have built
*--------------------------------------------------------------

frame change networks_single
format source target %4s
format bplace mig_out mig_in sch %8.4f
list in 1/8, noobs abbreviate(16)

* a flow weight is a share, so the weights leaving a node add up
* to one in every year
preserve
    split edge_id, parse("_") gen(node)
    collapse (sum) mig_out, by(year node1)
    format mig_out %8.4f
    list, noobs abbreviate(16)
restore

* an attribute weight is a log ratio, so it cancels along the
* reversed edge
preserve
    split edge_id, parse("_") gen(node)
    generate str24 pair = cond(node1 < node2, ///
                               node1 + "|" + node2, ///
                               node2 + "|" + node1)
    collapse (sum) sch, by(year pair)
    summarize sch
restore

*--------------------------------------------------------------
* The subnet weights themselves, in the multi-subnet frame
*--------------------------------------------------------------

frame change networks_multi
format feature source target %4s
format bplace_fratio bplace %7.4f
format mig_out_fratio mig_out %7.4f
format mig_in_fratio mig_in %7.4f
* every network in the frame, and beside each the share its subnet
* takes at the node
list in 1/9, noobs abbreviate(16)

* a subnet is a network of its own, so its weights add up to one
preserve
    split edge_id, parse("_") gen(node)
    collapse (sum) mig_out, by(year feature node1)
    format mig_out %8.4f
    list if year == 2018 & node1 == "van", noobs abbreviate(16)
restore

* and the shares those subnets take at the node add up to one
preserve
    split edge_id, parse("_") gen(node)
    bysort year feature node1: keep if _n == 1
    collapse (sum) mig_out_fratio, by(year node1)
    format mig_out_fratio %8.4f
    list, noobs abbreviate(16)
restore

frame change default

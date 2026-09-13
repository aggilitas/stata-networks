*! network_calc certification script
*! Run with the package on the adopath. The script stops at the first
*! failure.

cscript "network_calc" adofile network_calc

version 16.0
set more off

which network_calc

*==============================================================
* Synthetic data
*
* Six nodes, three periods, three subnets, a complete directed
* grid without self-loops. size carries the weight of a subnet
* at a node, value the quantity being measured.
*
* The single-subnet flow panel is the subnet panel added up over
* the feature, and the single-subnet attribute panel is the
* size-weighted mean of the subnet levels, so the two
* resolutions describe the same network.
*==============================================================

local N 6
local Y 3
local F 3

clear
set obs `N'
gen int i = _n
expand `N'
bysort i: gen int j = _n
drop if i == j
expand `Y'
bysort i j: gen int year = 2017 + _n
expand `F'
bysort i j year: gen int f = _n

gen str4 source  = "n" + string(i)
gen str4 target  = "n" + string(j)
gen str4 feature = "f" + string(f)

* subnet weights, constant within (year, feature, node)
gen double src_size = 1000 + 130*i + 70*f + 40*(year - 2017)
gen double tgt_size = 1000 + 130*j + 70*f + 40*(year - 2017)

* node levels, constant within (year, feature, node)
gen double src_lvl = 6 + 0.4*i + 0.9*f + 0.3*(year - 2017)
gen double tgt_lvl = 6 + 0.4*j + 0.9*f + 0.3*(year - 2017)

* edge quantities, varying over the edge
gen double qty_ij = 10 + 3*i + 2*j + f + (year - 2017)
gen double qty_ji = 10 + 3*j + 2*i + f + (year - 2017)

tempfile intdat flowdat flowsgl attrdat attrsgl

preserve
    keep year feature source target src_size tgt_size
    rename src_size source_size
    rename tgt_size target_size
    gen double source_value = source_size
    gen double target_value = target_size
    order year feature source target source_size source_value ///
          target_size target_value
    sort year feature source target
    qui save `intdat'
restore

preserve
    keep year feature source target src_size qty_ij tgt_size qty_ji
    rename (src_size qty_ij tgt_size qty_ji) ///
           (source_size source_value target_size target_value)
    sort year feature source target
    qui save `flowdat'

    collapse (sum) source_value target_value, by(year source target)
    sort year source target
    qui save `flowsgl'
restore

preserve
    keep year feature source target src_size src_lvl tgt_size tgt_lvl
    rename (src_size src_lvl tgt_size tgt_lvl) ///
           (source_size source_value target_size target_value)
    sort year feature source target
    qui save `attrdat'

    gen double sw = source_size * source_value
    gen double tw = target_size * target_value
    collapse (sum) sw source_size tw target_size, ///
        by(year source target)
    gen double source_value = sw / source_size
    gen double target_value = tw / target_size
    keep year source target source_value target_value
    sort year source target
    qui save `attrsgl'
restore

di as txt "certification data: `N' nodes, `Y' periods, `F' subnets"

*==============================================================
* 1. Weights leaving a node
*
* A subnet weight carries the share of its own subnet, so a
* subnet adds up to that share and only the subnets together
* add up to one. The single-subnet copy, being their sum, adds
* up to one as well. A single-subnet network computed from
* single-subnet data adds up to one directly.
*==============================================================

frames reset
use `flowsgl', clear
network_calc, type(flow) subnet(single) name(w)
frame networks_single {
    split edge_id, parse("_") gen(nd)
    collapse (sum) w, by(year nd1)
    assert reldif(w, 1) < 1e-12
}
di as res "1a flow single: weights leaving a node sum to one"

frames reset
use `flowdat', clear
network_calc, type(flow) subnet(multi) feature(feature) name(w)
frame networks_multi {
    split edge_id, parse("_") gen(nd)
    collapse (sum) w, by(year feature nd1)
    * a subnet adds up to its own share, which is below one
    assert w > 0 & w < 1
    collapse (sum) w, by(year nd1)
    assert reldif(w, 1) < 1e-12
}
di as res "1b flow multi: the subnets together sum to one"

frame networks_single {
    split edge_id, parse("_") gen(nd)
    collapse (sum) w, by(year nd1)
    assert reldif(w, 1) < 1e-12
}
di as res "1c flow multi: the combined copy sums to one"

frames reset
use `intdat', clear
network_calc, type(interaction) subnet(multi) feature(feature) ///
    name(w)
frame networks_multi {
    split edge_id, parse("_") gen(nd)
    collapse (sum) w, by(year feature nd1)
    assert w > 0 & w < 1
    collapse (sum) w, by(year nd1)
    assert reldif(w, 1) < 1e-12
}
di as res "1d interaction: the subnets together sum to one"

frame networks_single {
    split edge_id, parse("_") gen(nd)
    collapse (sum) w, by(year nd1)
    assert reldif(w, 1) < 1e-12
}
di as res "1e interaction: the combined copy sums to one"

*==============================================================
* 2. Attribute weights cancel along a reversed edge
*
* w_ij is a log ratio, so w_ij + w_ji is zero on a complete
* two-way grid. A log ratio does not add up over subnets, so an
* attribute network with subnets writes no single-subnet copy.
*==============================================================

frames reset
use `attrdat', clear
network_calc, type(attribute) subnet(multi) feature(feature) ///
    name(w)
frame networks_multi {
    split edge_id, parse("_") gen(nd)
    gen str12 pair = cond(nd1 < nd2, nd1 + "|" + nd2, ///
                                     nd2 + "|" + nd1)
    collapse (sum) w, by(year feature pair)
    assert abs(w) < 1e-12
}
di as res "2a attribute multi: each subnet cancels"

capture frame networks_single: describe
assert _rc != 0
di as res "2b attribute multi: writes no single-subnet copy"

frames reset
use `attrsgl', clear
network_calc, type(attribute) subnet(single) name(w)
frame networks_single {
    split edge_id, parse("_") gen(nd)
    gen str12 pair = cond(nd1 < nd2, nd1 + "|" + nd2, ///
                                     nd2 + "|" + nd1)
    collapse (sum) w, by(year pair)
    assert abs(w) < 1e-12
}
di as res "2c attribute single: cancels"

*==============================================================
* 3. Scaling the input leaves every weight alone
*
* Each template is built from ratios, so multiplying the whole
* input by a positive constant must not move a single weight.
* One constant above one and one below.
*==============================================================

foreach c in 1000 0.001 {
    foreach spec in "flow single flowsgl" "flow multi flowdat" ///
                    "interaction multi intdat" ///
                    "attribute single attrsgl" ///
                    "attribute multi attrdat" {
        local typ : word 1 of `spec'
        local sub : word 2 of `spec'
        local src : word 3 of `spec'
        if "`src'" == "flowsgl" local dat "`flowsgl'"
        if "`src'" == "flowdat" local dat "`flowdat'"
        if "`src'" == "intdat"  local dat "`intdat'"
        if "`src'" == "attrsgl" local dat "`attrsgl'"
        if "`src'" == "attrdat" local dat "`attrdat'"
        local opt = cond("`sub'" == "multi", "feature(feature)", "")
        local frm = "networks_single"
        if "`sub'" == "multi" & "`typ'" == "attribute" ///
            local frm = "networks_multi"

        tempfile base
        frames reset
        use "`dat'", clear
        network_calc, type(`typ') subnet(`sub') `opt' name(w)
        frame `frm': qui save "`base'", replace

        frames reset
        use "`dat'", clear
        qui replace source_value = source_value * `c'
        qui replace target_value = target_value * `c'
        if "`sub'" == "multi" {
            qui replace source_size = source_size * `c'
            qui replace target_size = target_size * `c'
        }
        network_calc, type(`typ') subnet(`sub') `opt' name(w)
        frame `frm' {
            rename w w_scaled
            if "`frm'" == "networks_multi" {
                qui merge 1:1 year feature edge_id using "`base'", ///
                    nogenerate
            }
            else {
                qui merge 1:1 year edge_id using "`base'", nogenerate
            }
            assert reldif(w_scaled, w) < 1e-12
        }
        di as res "3 `typ' `sub': unchanged when scaled by `c'"
    }
}

*==============================================================
* 4. direction(inflow)
*
* inflow exchanges the two indices and nothing else, so the
* weight written on edge i,j is the weight the same formula gives
* to edge j,i. The weights of a node therefore add up over the
* edges entering it rather than those leaving it, and an
* attribute weight, being a log ratio, simply changes sign.
*==============================================================

frames reset
use `flowsgl', clear
network_calc, type(flow) subnet(single) direction(inflow) name(w)
frame networks_single {
    split edge_id, parse("_") gen(nd)
    collapse (sum) w, by(year nd2)
    assert reldif(w, 1) < 1e-12
}
di as res "4a inflow flow single: weights entering a node sum to one"

frames reset
use `flowdat', clear
network_calc, type(flow) subnet(multi) feature(feature) ///
    direction(inflow) name(w)
frame networks_multi {
    split edge_id, parse("_") gen(nd)
    collapse (sum) w, by(year feature nd2)
    assert w > 0 & w < 1
    collapse (sum) w, by(year nd2)
    assert reldif(w, 1) < 1e-12
}
di as res "4b inflow flow multi: the subnets together sum to one"

frames reset
use `intdat', clear
network_calc, type(interaction) subnet(multi) feature(feature) ///
    direction(inflow) name(w)
frame networks_multi {
    split edge_id, parse("_") gen(nd)
    collapse (sum) w, by(year feature nd2)
    assert w > 0 & w < 1
    collapse (sum) w, by(year nd2)
    assert reldif(w, 1) < 1e-12
}
di as res "4c inflow interaction: the subnets together sum to one"

* an attribute weight is a log ratio, so reading the edge from the
* other end only changes its sign
frames reset
use `attrsgl', clear
network_calc, type(attribute) subnet(single) name(out)
use `attrsgl', clear
network_calc, type(attribute) subnet(single) direction(inflow) ///
    name(inw)
frame networks_single {
    assert reldif(inw, -out) < 1e-12
}
di as res "4d inflow attribute: the sign is the only difference"

* the outflow weight of i_j and the inflow weight of j_i are the
* same number: both divide the same edge by what leaves i
tempfile outflow
frames reset
use `flowsgl', clear
network_calc, type(flow) subnet(single) name(out)
frame networks_single: qui save "`outflow'", replace

frames reset
use `flowsgl', clear
network_calc, type(flow) subnet(single) direction(inflow) name(inw)
frame networks_single {
    split edge_id, parse("_") gen(nd)
    gen str12 rev = nd2 + "_" + nd1
    keep year rev inw
    rename rev edge_id
    qui merge 1:1 year edge_id using "`outflow'", ///
        keepusing(out) nogenerate
    assert reldif(inw, out) < 1e-12
}
di as res "4e inflow flow: the reversed edge carries the same weight"

*==============================================================
* 5. Joining a second network into a frame
*
* A frame is a panel of edges and every network in it is a
* column. The networks need not reach the same edges: the merge
* keeps the union, so no row is lost, and an edge a network does
* not reach weighs zero rather than nothing at all. Two networks
* that share no edge stack rather than sit side by side, and the
* command says so.
*==============================================================

frames reset
use `flowsgl', clear
qui count
local n_full = r(N)
network_calc, type(flow) subnet(single) name(wa)

* second network on a subset: one edge taken out
use `flowsgl', clear
qui drop if source == "n1" & target == "n2"
network_calc, type(flow) subnet(single) name(wb)

frame networks_single {
    qui count
    assert r(N) == `n_full'
    assert !missing(wa) & !missing(wb)
    assert wb == 0 if edge_id == "n1_n2"
    qui count if edge_id == "n1_n2"
    assert r(N) == 3
}
di as res "5a join: a smaller second network keeps every row"

* the other direction: the frame is built from the subset first
frames reset
use `flowsgl', clear
qui drop if source == "n1" & target == "n2"
network_calc, type(flow) subnet(single) name(wa)
use `flowsgl', clear
network_calc, type(flow) subnet(single) name(wb)

frame networks_single {
    qui count
    assert r(N) == `n_full'
    assert !missing(wa) & !missing(wb)
    assert !missing(source) & !missing(target)
    assert edge_id == source + "_" + target
    assert wa == 0 if edge_id == "n1_n2"
}
di as res "5b join: a larger second network fills the older column"

* both directions at once: each side reaches an edge the other
* does not
frames reset
use `flowsgl', clear
qui drop if source == "n1" & target == "n2"
network_calc, type(flow) subnet(single) name(wa)
use `flowsgl', clear
qui drop if source == "n3" & target == "n4"
network_calc, type(flow) subnet(single) name(wb)

frame networks_single {
    qui count
    assert r(N) == `n_full'
    assert !missing(wa) & !missing(wb)
    assert !missing(source) & !missing(target)
    assert edge_id == source + "_" + target
    assert wa == 0 if edge_id == "n1_n2"
    assert wb == 0 if edge_id == "n3_n4"
}
di as res "5c join: both sides filled in the same call"

* an attribute column is filled the same way
frames reset
use `attrsgl', clear
network_calc, type(attribute) subnet(single) name(ga)
use `attrsgl', clear
qui drop if source == "n1" & target == "n2"
network_calc, type(attribute) subnet(single) name(gb)

frame networks_single {
    assert !missing(ga) & !missing(gb)
    assert gb == 0 if edge_id == "n1_n2"
}
di as res "5d join: an attribute column is filled too"

* no shared edge at all: the frame becomes the two blocks stacked
frames reset
use `flowsgl', clear
network_calc, type(flow) subnet(single) name(wa)
frame networks_single {
    qui count
    local n_before = r(N)
}
use `flowsgl', clear
qui replace source = "z" + source
qui replace target = "z" + target
network_calc, type(flow) subnet(single) name(wb)
frame networks_single {
    qui count
    assert r(N) == 2 * `n_before'
    qui count if wa != 0 & wb != 0
    assert r(N) == 0
}
di as res "5e join: a disjoint network stacks, nothing overlaps"

*==============================================================
* 6. What the command refuses
*
* Data it cannot make a network of is refused rather than turned
* into a weight that reads as defined, and a name that would be
* lost or would overwrite a column is refused before anything is
* computed.
*==============================================================

frames reset
use `flowsgl', clear
qui replace source_value = . in 1
capture network_calc, type(flow) subnet(single) name(w)
assert _rc == 416
capture frame networks_single: describe
assert _rc != 0
di as res "6a refuses a missing value, and writes nothing"

frames reset
use `flowsgl', clear
qui replace source_value = -1 in 1
capture network_calc, type(flow) subnet(single) name(w)
assert _rc == 411
di as res "6b refuses a negative flow"

frames reset
use `flowdat', clear
qui replace source_size = -1 in 1
capture network_calc, type(flow) subnet(multi) feature(feature) ///
    name(w)
assert _rc == 411
di as res "6c refuses a negative subnet size"

frames reset
use `attrsgl', clear
qui replace target_value = 0 in 1
capture network_calc, type(attribute) subnet(single) name(w)
assert _rc == 411
di as res "6d refuses a non-positive attribute value"

frames reset
use `flowsgl', clear
foreach bad in year source target edge_id feature {
    capture network_calc, type(flow) subnet(single) name(`bad')
    assert _rc == 198
}
di as res "6e refuses the five names the frames carry themselves"

frames reset
use `flowsgl', clear
network_calc, type(flow) subnet(single) name(w)
use `flowsgl', clear
capture network_calc, type(flow) subnet(single) name(w)
assert _rc == 110
frame networks_single {
    qui describe, short
    assert r(k) == 5
}
di as res "6f refuses a name the frame already holds"

* size is the share of the subnet in what leaves the node, so a
* subnet out of which nothing travels carries a size of zero. Its
* edges weigh zero, the share it would have held goes to the
* subnets that did move, and the node still adds up to one
frames reset
use `flowdat', clear
qui replace source_value = 0 if source == "n1" & feature == "f1"
qui replace source_size  = 0 if source == "n1" & feature == "f1"
network_calc, type(flow) subnet(multi) feature(feature) name(w)
frame networks_multi {
    split edge_id, parse("_") gen(nd)
    qui count if nd1 == "n1" & feature == "f1" & w != 0
    assert r(N) == 0
    qui count if missing(w)
    assert r(N) == 0
    collapse (sum) w, by(year nd1)
    assert reldif(w, 1) < 1e-12
}
di as res "6g an empty subnet weighs zero, the node still sums to one"

di as res _n "all network_calc certification tests passed"

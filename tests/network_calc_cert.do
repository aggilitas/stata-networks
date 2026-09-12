*! network_calc certification script
*! Run with the package on the adopath. To include the comparison
*! against the published version, point a global at a checkout of the
*! v1.0.0-kbs tag before running:
*!
*!     global NETCALC_KBS "/path/to/the/tag/checkout"
*!     do network_calc_cert.do
*!
*! The script stops at the first failure.

* read before cscript: cscript clears globals
local kbs "$NETCALC_KBS"

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
* 4. Comparison with the published version
*
* Skipped unless a checkout of v1.0.0-kbs is pointed at. The
* three configurations below must reproduce it exactly. The
* certification data sets size equal to value for interaction,
* which is what the published version read, so the comparison
* stays meaningful after the input gained the size columns.
*
* The configurations expected to differ are not compared:
* direction(inflow) was not applied by the published version, a
* multi-subnet flow weight now carries the share of its subnet,
* and an attribute network with subnets no longer writes a
* single-subnet copy.
*==============================================================

if "`kbs'" == "" {
    di as txt "4 skipped: set global NETCALC_KBS to compare " ///
              "against v1.0.0-kbs"
}
else {
    foreach spec in "interaction multi intdat" ///
                    "flow single flowsgl" ///
                    "attribute single attrsgl" {
        local typ : word 1 of `spec'
        local sub : word 2 of `spec'
        local src : word 3 of `spec'
        if "`src'" == "flowsgl" local dat "`flowsgl'"
        if "`src'" == "intdat"  local dat "`intdat'"
        if "`src'" == "attrsgl" local dat "`attrsgl'"
        local opt = cond("`sub'" == "multi", "feature(feature)", "")

        tempfile kbsout
        frames reset
        discard
        adopath ++ "`kbs'/code"
        adopath ++ "`kbs'/code/helpers"
        use "`dat'", clear
        network_calc, type(`typ') subnet(`sub') `opt' name(w)
        frame networks_single: qui save "`kbsout'", replace

        * take the published version back off the adopath, or the
        * current code would never be reached on the next pass
        adopath - "`kbs'/code/helpers"
        adopath - "`kbs'/code"

        frames reset
        discard
        use "`dat'", clear
        network_calc, type(`typ') subnet(`sub') `opt' name(w)
        frame networks_single {
            rename w w_now
            qui merge 1:1 year edge_id using "`kbsout'", ///
                nogenerate
            assert reldif(w_now, w) < 1e-12
        }
        di as res "4 `typ' `sub': reproduces v1.0.0-kbs"
    }
}

di as res _n "all network_calc certification tests passed"

*! network_calc certification script
*! Run with the package on the adopath. To include the comparison
*! against the published version, point a global at a checkout of the
*! v1.0.0-kbs tag before running:
*!
*!     global NETCALC_KBS "/path/to/stata-networks-v1.0.0-kbs"
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
* Six nodes, three periods, three features, a complete directed
* grid without self-loops. Two panels are needed because the two
* kinds of input differ: a node level is repeated on every edge
* of its node, while a flow belongs to the edge itself.
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

* node levels: constant within (year, feature, node)
gen double lvl_i = 1000 + 100*i + 10*f + 5*(year - 2017)
gen double lvl_j = 1000 + 100*j + 10*f + 5*(year - 2017)

* edge quantities: vary over the edge
gen double qty_ij = 10 + 3*i + 2*j + f + (year - 2017)
gen double qty_ji = 10 + 3*j + 2*i + f + (year - 2017)

tempfile nodedat flowdat
preserve
    keep year feature source target lvl_i lvl_j
    rename lvl_i source_value
    rename lvl_j target_value
    sort year feature source target
    qui save `nodedat'
restore
    keep year feature source target qty_ij qty_ji
    rename qty_ij source_value
    rename qty_ji target_value
    sort year feature source target
    qui save `flowdat'

di as txt "certification data: `N' nodes, `Y' periods, `F' features"

*==============================================================
* 1. Weights leaving a node
*
* flow: every subnet is a whole network of its own, so its
* weights sum to one, and so do the weights of the combined
* single-subnet copy.
*
* interaction: a subnet weight already carries the share of its
* subnet, so a subnet sums to that share, and only the sum over
* all subnets is one. The combined copy is one as well.
*==============================================================

* --- flow, single subnet ---
frames reset
use `flowdat', clear
collapse (sum) source_value target_value, by(year source target)
network_calc, type(flow) subnet(single) name(w)
frame networks_single {
    split edge_id, parse("_") gen(nd)
    collapse (sum) w, by(year nd1)
    assert reldif(w, 1) < 1e-12
}
di as res "1a flow single: weights leaving a node sum to one"

* --- flow, multi subnet, inside each subnet ---
frames reset
use `flowdat', clear
network_calc, type(flow) subnet(multi) feature(feature) name(w)
frame networks_multi {
    split edge_id, parse("_") gen(nd)
    collapse (sum) w, by(year feature nd1)
    assert reldif(w, 1) < 1e-12
}
di as res "1b flow multi: each subnet sums to one"

* --- flow, multi subnet, combined copy ---
frame networks_single {
    split edge_id, parse("_") gen(nd)
    collapse (sum) w, by(year nd1)
    assert reldif(w, 1) < 1e-12
}
di as res "1c flow multi: the combined copy sums to one"

* --- interaction, subnet shares and their total ---
frames reset
use `nodedat', clear
network_calc, type(interaction) subnet(multi) feature(feature) ///
    name(w)
frame networks_multi {
    split edge_id, parse("_") gen(nd)
    collapse (sum) w, by(year feature nd1)
    * a subnet sums to its own share, which is below one
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
* two-way grid. This must hold for a subnet, for the combined
* copy, and without a feature at all.
*==============================================================

frames reset
use `nodedat', clear
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

frame networks_single {
    split edge_id, parse("_") gen(nd)
    gen str12 pair = cond(nd1 < nd2, nd1 + "|" + nd2, ///
                                     nd2 + "|" + nd1)
    collapse (sum) w, by(year pair)
    assert abs(w) < 1e-12
}
di as res "2b attribute multi: the combined copy cancels"

frames reset
use `nodedat', clear
collapse (sum) source_value target_value, by(year source target)
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
    foreach spec in "flow single" "flow multi" ///
                    "interaction multi" "attribute single" ///
                    "attribute multi" {
        local typ : word 1 of `spec'
        local sub : word 2 of `spec'
        local dat = cond("`typ'" == "flow", "`flowdat'", ///
                                            "`nodedat'")
        local opt = cond("`sub'" == "multi", "feature(feature)", "")

        frames reset
        use "`dat'", clear
        if "`sub'" == "single" {
            collapse (sum) source_value target_value, ///
                by(year source target)
        }
        tempfile base
        network_calc, type(`typ') subnet(`sub') `opt' name(w)
        frame networks_single: qui save "`base'", replace

        frames reset
        use "`dat'", clear
        if "`sub'" == "single" {
            collapse (sum) source_value target_value, ///
                by(year source target)
        }
        qui replace source_value = source_value * `c'
        qui replace target_value = target_value * `c'
        network_calc, type(`typ') subnet(`sub') `opt' name(w)
        frame networks_single {
            rename w w_scaled
            qui merge 1:1 year edge_id using "`base'", ///
                nogenerate
            assert reldif(w_scaled, w) < 1e-12
        }
        di as res "3 `typ' `sub': unchanged when scaled by `c'"
    }
}

*==============================================================
* 4. Comparison with the published version
*
* Skipped unless a checkout of v1.0.0-kbs is pointed at. Three
* results must reproduce it exactly. Three are expected to
* differ, each for a reason recorded in the history:
*
*   the interaction node total is now a double, so a node total
*   above 16,777,216 no longer rounds; below that, nothing moves
*
*   the single-subnet copy of a multi-subnet flow or attribute
*   network is now built from the data rather than by adding the
*   subnet weights
*==============================================================

if "`kbs'" == "" {
    di as txt "4 skipped: set global NETCALC_KBS to compare " ///
              "against v1.0.0-kbs"
}
else {
    foreach spec in "interaction multi nodedat" ///
                    "flow single flowdat" ///
                    "attribute single nodedat" {
        local typ : word 1 of `spec'
        local sub : word 2 of `spec'
        local src : word 3 of `spec'
        local dat = cond("`src'" == "flowdat", "`flowdat'", ///
                                               "`nodedat'")
        local opt = cond("`sub'" == "multi", "feature(feature)", "")

        tempfile kbsout
        frames reset
        discard
        adopath ++ "`kbs'/code"
        adopath ++ "`kbs'/code/helpers"
        use "`dat'", clear
        if "`sub'" == "single" {
            collapse (sum) source_value target_value, ///
                by(year source target)
        }
        network_calc, type(`typ') subnet(`sub') `opt' name(w)
        frame networks_single: qui save "`kbsout'", replace

        * take the published version back off the adopath, or the
        * current code would never be reached on the next pass
        adopath - "`kbs'/code/helpers"
        adopath - "`kbs'/code"

        frames reset
        discard
        use "`dat'", clear
        if "`sub'" == "single" {
            collapse (sum) source_value target_value, ///
                by(year source target)
        }
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

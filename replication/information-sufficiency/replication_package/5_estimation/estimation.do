*==============================================================================
* TCLF sector dependence on the eighteen-country subnet R, 2016-2025: final run.
*
* Nodes: BE BG DE DK EE ES FR GR HR HU IT LT LV PL PT RO SE SI (306 directed
* corridors). Networks: the export networks of 18 TCLF sectors (HS 41-43, 50-65
* without 55), the layers of one multiplex. On the edge i->j:
*   export_k = exports of i to j in k / world exports of i in k (outflow, REST
*              closure, exporter declaration only, absent Comext cell = zero)
*   controls, ln(A_j / A_i) of
*     productivity: manufacturing real value added per hour worked (quarterly
*                   accounts, sum of four quarters),
*     finance:      real cost of bank credit to non-financial corporations,
*                   (1 + i/100) / (1 + pi/100), i = revolving loans and overdrafts
*                   (ECB MIR), pi = manufacturing producer prices,
*     electricity:  non-household price,
*   each in levels or as its yearly change, as the unit-root step decides.
*
* Sequence:
*   1. construction with network_calc, one input file per network, and checks;
*   2. panel unit roots, Fisher-type Phillips-Perron, once per variable (levels
*      2016-2025; a corridor constant over 2017-2025 or 2016-2024 has no
*      statistic and is left out; attributes tested once per unordered pair); weights
*      are never differenced, an attribute that does not reject enters as its
*      yearly change;
*   3. screen: export_a on export_b and the controls, reghdfe, for all 306
*      ordered pairs a != b, corridor effects absorbed, SE clustered on the
*      corridor;
*   4. results.
* The permutation inference of the paper (MRQAP) is computed afterwards by
* mrqap.py in this folder, from the same input files and the unit-root outcome
* written here (results/unit_roots.csv); it also checks that its coefficients
* and clustered standard errors equal those of results/screen_models.csv.
*
* Inputs, written by ../3_inputs/build_inputs.py, one file per network
* in ../3_inputs/networks/ (year source target source_value target_value): export_<hs>.csv,
* attr_prod.csv, attr_fin.csv, attr_elec.csv; and ../3_inputs/check_weights.csv.
* Output, in results/: unit_roots and screen_models (306 models), each as .dta
* and .csv; log estimation.log.
* Break stops the run at any point.
* Requirements: ftools reghdfe network_calc (sources and versions in README.md)
*==============================================================================
version 17
clear all
set more off
set varabbrev off
capture log close
* Replication package: run this file from the folder that holds it (5_estimation),
* e.g.  cd "<package folder>/5_estimation"  and then  do estimation.do
* (the original run changed here to the authors' local copy of this folder)
confirm file "estimation.do"
capture mkdir "results"
log using "estimation.log", replace text

which network_calc
foreach p in ftools reghdfe {
    capture which `p'
    if _rc {
        display as error "`p' is not installed (ssc install `p')"
        exit 111
    }
}

* ---- settings ----------------------------------------------------------------
local R  "BE BG DE DK EE ES FR GR HR HU IT LT LV PL PT RO SE SI"
local HS "41 42 43 50 51 52 53 54 56 57 58 59 60 61 62 63 64 65"
local alpha 0.05
local nR : word count `R'
local nE = `nR' * (`nR' - 1)
local nHS : word count `HS'
* -----------------------------------------------------------------------------

*----------------------------------------------------------------------------
* 1. Construction, one file per network
*----------------------------------------------------------------------------
foreach k of local HS {
    import delimited using "../3_inputs/networks/export_`k'.csv", clear varnames(1) asdouble stringcols(2 3)
    * whole euro values below the long limit are read as long, which holds
    * them exactly; only float would lose digits
    confirm numeric variable source_value target_value
    foreach c in source_value target_value {
        local t : type `c'
        if "`t'" == "float" {
            display as error "../3_inputs/networks/export_`k'.csv: `c' read as float"
            exit 7
        }
    }
    assert inrange(year, 2016, 2025)
    assert source != target
    assert !missing(source_value, target_value)
    assert source_value >= 0 & source_value == target_value
    gen byte inR  = strpos(" `R' ", " " + source + " ") > 0 & strpos(" `R' ", " " + target + " ") > 0
    gen byte rest = target == "REST" & strpos(" `R' ", " " + source + " ") > 0
    assert inR | rest
    bysort year: egen long nRR = total(inR)
    bysort year: egen long nREST = total(rest)
    assert nRR == `nE' & nREST == `nR'                  // complete R mesh, one REST row per node
    quietly tabulate year
    assert r(r) == 10
    drop inR rest nRR nREST
    network_calc, type(flow) subnet(single) direction(outflow) name(export_`k')
}

foreach a in prod fin elec {
    import delimited using "../3_inputs/networks/attr_`a'.csv", clear varnames(1) asdouble stringcols(2 3)
    confirm numeric variable source_value target_value
    foreach c in source_value target_value {
        local t : type `c'
        if "`t'" == "float" {
            display as error "../3_inputs/networks/attr_`a'.csv: `c' read as float"
            exit 7
        }
    }
    assert inrange(year, 2015, 2025)
    assert source != target & !missing(source_value, target_value)
    assert source_value > 0 & target_value > 0
    gen byte inR = strpos(" `R' ", " " + source + " ") > 0 & strpos(" `R' ", " " + target + " ") > 0
    assert inR
    bysort year: egen long nRR = total(inR)
    assert nRR == `nE'
    quietly tabulate year
    assert r(r) == 11
    drop inR nRR
    network_calc, type(attribute) subnet(single) name(attr_`a')
}

frame change networks_single

* 1a. row sums: export weights sum to one at the source, REST included; a
*     source whose world exports in a sector are zero weighs zero
foreach k of local HS {
    bysort year source: egen double rs = total(export_`k')
    assert abs(rs - 1) < 1e-10 | rs == 0 if year >= 2016 & source != "REST"
    drop rs
}

* 1b. direct formula: the weights against the recorded world totals
frame create chk
frame chk {
    import delimited using "../3_inputs/check_weights.csv", clear varnames(1) asdouble stringcols(2 3 4)
    reshape wide export_direct, i(year source target) j(hs) string
    gen edge_id = source + "_" + target
    keep year edge_id export_direct*
}
frlink m:1 year edge_id, frame(chk)
frget export_direct*, from(chk)
foreach k of local HS {
    gen double d1 = abs(export_`k' - export_direct`k') if !missing(export_direct`k')
    quietly count if !missing(d1)
    assert r(N) == `nE' * 10
    assert d1 < 1e-10 if !missing(d1)
    drop d1
}
drop chk export_direct*
frame drop chk
display "construction matches the direct formula"

* 1c. keep the R mesh; the attribute inputs bring 2015 rows on which the trade
*     columns were filled with zero by the join: set them to missing
gen byte inR = strpos(" `R' ", " " + source + " ") > 0 & strpos(" `R' ", " " + target + " ") > 0
keep if inR
drop inR
foreach v of varlist export_* {
    quietly replace `v' = . if year == 2015
}
egen long cid = group(edge_id)
bysort year: gen long n_edges = _N
assert n_edges == `nE'
drop n_edges
xtset cid year
assert r(balanced) == "strongly balanced"

*----------------------------------------------------------------------------
* 2. Unit roots in levels, once per variable
*----------------------------------------------------------------------------
* Every variable is tested on its levels 2016-2025: the first test observation
* is 2017 with its lag in 2016. A corridor whose series does not move over
* 2017-2025 or over 2016-2024 has no statistic and is left out; the corridors
* left out are posted: constant over 2016-2025, and constant in one window only.
local A ""
tempname ur
postfile `ur' str24 variable double(p_fisher_pp n_panels n_constant n_one_window) using "results/unit_roots.dta", replace
foreach v of varlist export_* attr_* {
    local half ""
    if substr("`v'", 1, 5) == "attr_" local half "& source < target"
    tempvar sdv sdy sdl
    quietly bysort cid: egen double `sdv' = sd(cond(year >= 2016, `v', .))
    quietly bysort cid: egen double `sdy' = sd(cond(year >= 2017, `v', .))
    quietly bysort cid: egen double `sdl' = sd(cond(inrange(year, 2016, 2024), `v', .))
    sort cid year
    local ok "`sdy' > 0 & `sdl' > 0"
    quietly count if year == 2016 & `ok' `half'
    local npan = r(N)
    quietly count if year == 2016 & `sdv' == 0 `half'
    local ncon = r(N)
    quietly count if year == 2016 & `sdv' > 0 & !(`ok') `half'
    local none = r(N)
    quietly xtunitroot fisher `v' if year >= 2017 & `ok' `half', pperron lags(1)
    local p = r(p_P)
    if missing(`p') {
        display as error "`v': the unit-root test returned no p value"
        exit 459
    }
    assert r(df_P) == 2 * `npan'
    post `ur' ("`v'") (`p') (`npan') (`ncon') (`none')
    drop `sdv' `sdy' `sdl'
    display "`v': p = " %6.4f `p' " on `npan' corridors; left out: `ncon' constant, `none' constant in one window"
    if substr("`v'", 1, 5) == "attr_" {
        local a = substr("`v'", 6, .)
        if `p' >= `alpha' {
            gen double use_`a' = D.`v'
            display "   attr_`a' enters as its yearly change"
            * the yearly change is tested with the same test on 2016-2025 (the
            * change in 2016 reads the recorded 2015 level)
            quietly xtunitroot fisher use_`a' if year >= 2017 & source < target, pperron lags(1)
            local pd = r(p_P)
            if missing(`pd') {
                display as error "D.`v': the unit-root test returned no p value"
                exit 459
            }
            assert r(df_P) == 2 * `npan'
            post `ur' ("D.`v'") (`pd') (`npan') (0) (0)
            display "   D.`v': p = " %9.3e `pd'
        }
        else {
            gen double use_`a' = `v'
            display "   attr_`a' enters in levels"
        }
        local A "`A' use_`a'"
    }
}
postclose `ur'
sort cid year
drop if year == 2015
xtset cid year
assert _N == `nE' * 10
assert !missing(use_prod, use_fin, use_elec)

*----------------------------------------------------------------------------
* 3. Models: export_a on export_b and the controls, reghdfe
*----------------------------------------------------------------------------
tempname res
postfile `res' str2 y_sector str2 x_sector str7 model ///
    double(b_x se_x p_x b_prod se_prod p_prod b_fin se_fin p_fin ///
           b_elec se_elec p_elec r2_within N N_clust) ///
    using "results/screen_models.dta", replace

local nm = 0
foreach a of local HS {
    foreach b of local HS {
        if "`a'" == "`b'" continue
        local x "export_`b'"
        capture quietly reghdfe export_`a' `x' `A', absorb(cid) vce(cluster cid)
        local rc = _rc
        if `rc' == 1 exit 1                               // Break
        foreach t in x prod fin elec {
            local b_`t' = .
            local s_`t' = .
            local p_`t' = .
        }
        local r2   = .
        local nobs = .
        local ncl  = .
        local model "failed"
        if `rc' == 0 {
            local model "reghdfe"
            local df = e(df_r)
            foreach v in `x' `A' {
                if "`v'" == "`x'" local t "x"
                else local t = substr("`v'", 5, .)
                capture local bb = _b[`v']
                if _rc local bb = .
                capture local ss = _se[`v']
                if _rc local ss = .
                * an omitted regressor keeps b, se and p missing
                if `ss' < . & `ss' > 0 {
                    local b_`t' = `bb'
                    local s_`t' = `ss'
                    local p_`t' = 2 * ttail(`df', abs(`bb' / `ss'))
                }
            }
            local r2   = e(r2_within)
            local nobs = e(N)
            local ncl  = e(N_clust)
        }
        post `res' ("`a'") ("`b'") ("`model'") ///
            (`b_x') (`s_x') (`p_x') (`b_prod') (`s_prod') (`p_prod') ///
            (`b_fin') (`s_fin') (`p_fin') (`b_elec') (`s_elec') (`p_elec') ///
            (`r2') (`nobs') (`ncl')
        local ++nm
    }
    display "sector `a' done"
}
postclose `res'
assert `nm' == `nHS' * (`nHS' - 1)

*----------------------------------------------------------------------------
* 4. Results (5% level, corridor clustering; MRQAP in mrqap.py)
*----------------------------------------------------------------------------
use "results/unit_roots.dta", clear
export delimited using "results/unit_roots.csv", replace
list, noobs clean
use "results/screen_models.dta", clear
export delimited using "results/screen_models.csv", replace
tabulate model
gen byte sig = p_x < 0.05 if !missing(p_x)
gen byte sign = cond(b_x > 0, 1, -1) if sig == 1
label define sign -1 "negative" 1 "positive"
label values sign sign
tabulate sig, missing
tabulate sign
* significant models, by dependent sector
list y_sector x_sector b_x p_x if sig == 1, noobs sepby(y_sector)
* pairs significant in both directions
preserve
keep if sig == 1
keep y_sector x_sector b_x
tempfile s
save `s'
rename (y_sector x_sector b_x) (x_sector y_sector b_rev)
merge 1:1 y_sector x_sector using `s', keep(match) nogenerate
keep if y_sector < x_sector
list y_sector x_sector b_x b_rev, noobs clean
restore
foreach v in prod fin elec {
    count if p_`v' < 0.05 & !missing(p_`v')
}
log close

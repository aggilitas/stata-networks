*! _netcalc_attribute 2.2.0
*! Helper function for calculating attribute network edge values
*! Formula: w_ij = ln(A_j / A_i). Under subnet(multi) the value inside
*! a subnet is w_ij^X = ln(A_j^X / A_i^X), zero where one of the two
*! nodes does not hold the subnet, and the single-subnet network is
*! built from the node levels A_i = sum_X S_i^X A_i^X / sum_X S_i^X

program define _netcalc_attribute, rclass
    version 16.0
    syntax, Subnet(string) Direction(string) ///
            [Feature(varname) SINGLEfile(string) DEBUG]

    * Validate subnet type
    if !inlist("`subnet'", "single", "multi") {
        di as error "subnet() must be single or multi"
        exit 198
    }

    * For multi-subnet, feature is required
    if "`subnet'" == "multi" & "`feature'" == "" {
        di as error "feature() required for multi-subnet attribute network"
        exit 198
    }

    * Validate required variables
    if "`subnet'" == "multi" {
        local required_vars year `feature' source target edge_id ///
                            source_size source_value ///
                            target_size target_value
    }
    else {
        local required_vars year source target edge_id ///
                            source_value target_value
    }

    foreach var of local required_vars {
        capture confirm variable `var'
        if _rc {
            di as error "Variable `var' not found in dataset"
            exit 111
        }
    }

    * An inflow network is the same computation read from the other
    * end of the edge. Nothing in the data moves: the roles are
    * assigned to the other columns and the rest of the routine reads
    * through these names. The edge keeps its own orientation, and so
    * does edge_id, built by the caller from source and target as they
    * stand.
    if "`direction'" == "inflow" {
        local nsrc target
        local ntgt source
        local ssrc target_size
        local vsrc target_value
        local vtgt source_value
    }
    else {
        local nsrc source
        local ntgt target
        local ssrc source_size
        local vsrc source_value
        local vtgt target_value
    }

    if "`debug'" != "" {
        di as text "_netcalc_attribute: Starting calculation"
        di as text "  Subnet: `subnet'"
        if "`subnet'" == "multi" {
            di as text "  Feature variable: `feature'"
        }
        di as text "  Observations: " _N
    }

    * The log ratio is defined only for positive levels, which is the
    * domain the template is for. A level outside it is a fault in
    * the data, not an edge without a value, so it stops the command
    * rather than leaving a missing value behind. Under subnet(multi)
    * the level of a subnet at a node that does not hold it, one whose
    * size there is zero, is not read.
    if "`subnet'" == "multi" {
        qui count if (source_value <= 0 & source_size != 0) | ///
                     (target_value <= 0 & target_size != 0)
    }
    else {
        qui count if `vsrc' <= 0 | `vtgt' <= 0
    }
    if r(N) > 0 {
        di as error "attributes can not be zero or negative"
        exit 411
    }

    * Calculate attribute network edge values
    * Formula: w_ij = ln(A_j / A_i). Under inflow the two values change
    * places, which is what flips the sign of the ratio.
    local n_absent = 0

    if "`subnet'" == "single" {
        qui {
            tempvar edge_weight
            gen double `edge_weight' = ln(`vtgt' / `vsrc')

            keep year source target edge_id `edge_weight'
            rename `edge_weight' edge_value
            order year source target edge_id edge_value
        }
    }
    else {
        tempname L
        tempvar edge_weight netcalc_fratio tfirst runsrc total_source ///
                num link_s link_t lvl_s lvl_t single

        * The level of each node: the levels of its subnets, each
        * weighted by its size. On the complete mesh every node leaves
        * edges, so the rows it leaves hold all its subnets; one row of
        * each subnet is read, and a subnet the node does not hold adds
        * nothing, whatever stands in its level.
        capture frame drop `L'
        frame put year `feature' source source_size source_value, ///
            into(`L')
        frame `L' {
            qui bysort year `feature' source: keep if _n == 1
            qui gen double `num' = cond(source_size == 0, 0, ///
                                        source_size * source_value)
            qui collapse (sum) `num' source_size, by(year source)
            qui gen double level = `num' / source_size
            qui count if missing(level)
            local n_nolevel = r(N)
            keep year source level
            rename source node
        }
        if `n_nolevel' > 0 {
            di as error "the sizes of a node sum to zero, so it has no level"
            capture frame drop `L'
            exit 459
        }

        qui {
            * Inside a subnet the value is the log-ratio of the two
            * levels of that subnet. Where one of the two nodes does
            * not hold the subnet, the attribute pushes and pulls
            * nothing along the edge: the value is zero, and the rows
            * are counted.
            count if source_size == 0 | target_size == 0
            local n_absent = r(N)
            gen double `edge_weight' = ///
                cond(source_size == 0 | target_size == 0, 0, ///
                     ln(`vtgt' / `vsrc'))

            * The ratio of the subnet at its node, as under the
            * interaction template: the size is read once for each
            * subnet of the node, from one of its rows.
            bysort year `feature' `nsrc' (`ntgt'): ///
                gen byte `tfirst' = (_n == 1)
            bysort year `nsrc': ///
                gen double `runsrc' = sum(`ssrc' * `tfirst')
            by year `nsrc': gen double `total_source' = `runsrc'[_N]
            gen double `netcalc_fratio' = `ssrc' / `total_source'
            replace `netcalc_fratio' = 0 if `total_source' == 0

            * The single-subnet network is not put together from the
            * subnet values: the levels are reduced to the node first,
            * and the value of the edge is the log-ratio of the two
            * node levels, so it changes sign with the edge like any
            * attribute value.
            frlink m:1 year source, frame(`L' year node) ///
                generate(`link_s')
            frget `lvl_s' = level, from(`link_s')
            frlink m:1 year target, frame(`L' year node) ///
                generate(`link_t')
            frget `lvl_t' = level, from(`link_t')
            if "`direction'" == "inflow" {
                gen double `single' = ln(`lvl_s' / `lvl_t')
            }
            else {
                gen double `single' = ln(`lvl_t' / `lvl_s')
            }
        }

        * The caller joins the single-subnet network to its frame from
        * this file: one row for each edge.
        if `"`singlefile'"' != "" {
            tempname SG
            capture frame drop `SG'
            frame put year source target edge_id `single', into(`SG')
            frame `SG' {
                qui bysort year source target: keep if _n == 1
                rename `single' edge_value
                order year source target edge_id edge_value
                qui save `"`singlefile'"', replace
            }
            capture frame drop `SG'
        }
        capture frame drop `L'

        qui {
            keep year `feature' source target edge_id ///
                 `edge_weight' `netcalc_fratio'
            rename `edge_weight' edge_value
            rename `netcalc_fratio' netcalc_fratio
            rename `feature' feature
            order year feature source target edge_id ///
                  netcalc_fratio edge_value
        }
    }

    if "`debug'" != "" {
        di as text "_netcalc_attribute: Calculation completed"
        di as text "  Output observations: " _N
        sum edge_value, detail
    }

    * Return statistics. No total is taken, so no total is zero.
    sum edge_value, meanonly
    return scalar mean_weight = r(mean)
    return scalar n_edges = _N
    return scalar n_zero_totals = 0
    return scalar n_zero_sizes = 0
    return scalar n_absent = `n_absent'

end

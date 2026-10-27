*! _netcalc_attribute 2.1.0
*! Helper function for calculating attribute network edge values
*! Formula: w_ij = ln(A_j / A_i)

program define _netcalc_attribute, rclass
    version 16.0
    syntax, Direction(string) [DEBUG]

    * An attribute describes the node, so it has no subnets: the
    * caller passes one level per node and refuses subnet(multi).
    local required_vars year source target source_value target_value

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
    * through these names. The edge keeps its own orientation, so
    * edge_id is built from source and target as they stand.
    if "`direction'" == "inflow" {
        local vsrc target_value
        local vtgt source_value
    }
    else {
        local vsrc source_value
        local vtgt target_value
    }

    if "`debug'" != "" {
        di as text "_netcalc_attribute: Starting calculation"
        di as text "  Observations: " _N
    }

    * The log ratio is defined only for positive levels, which is the
    * domain the template is for. A value outside it is a fault in the
    * data, not an edge without a weight, so it stops the command
    * rather than leaving a missing weight behind.
    qui count if `vsrc' <= 0 | `vtgt' <= 0
    if r(N) > 0 {
        di as error "attributes can not be zero or negative"
        exit 411
    }

    * Calculate attribute network edge values
    * Formula: w_ij = ln(A_j / A_i). Under inflow the two values change
    * places, which is what flips the sign of the ratio.
    qui {
        tempvar edge_weight edge_id
        gen double `edge_weight' = ln(`vtgt' / `vsrc')
        gen `edge_id' = source + "_" + target

        keep year source target `edge_id' `edge_weight'
        rename `edge_id' edge_id
        rename `edge_weight' edge_value
        order year source target edge_id edge_value
    }

    if "`debug'" != "" {
        di as text "_netcalc_attribute: Calculation completed"
        di as text "  Output observations: " _N
        sum edge_value, detail
    }

    * Return statistics
    sum edge_value, meanonly
    return scalar mean_weight = r(mean)
    return scalar n_edges = _N

end

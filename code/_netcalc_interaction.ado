*! _netcalc_interaction 2.0.0
*! Helper function for calculating interaction network edge weights
*! Formula: e_ij^X = (S_i^X / S_i) * (v_j^X / sum_{k!=i} v_k^X)

program define _netcalc_interaction, rclass
    version 16.0
    syntax, Feature(varname) Direction(string) [DEBUG]
    
    * Validate required variables
    local required_vars year `feature' source target ///
                        source_size source_value ///
                        target_size target_value
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
        local nsrc target
        local ntgt source
        local ssrc target_size
        local vtgt source_value
    }
    else {
        local nsrc source
        local ntgt target
        local ssrc source_size
        local vtgt target_value
    }

    if "`debug'" != "" {
        di as text "_netcalc_interaction: Starting calculation"
        di as text "  Feature variable: `feature'"
        di as text "  Observations: " _N
    }
    
    * The network inside the subnet divides the quantity the subnet
    * carries among the nodes other than the source. A node can hold
    * none of it, but it cannot hold a negative amount.
    qui count if `vtgt' < 0
    if r(N) > 0 {
        di as error "interaction values can not be negative"
        exit 411
    }

    * Calculate interaction network weights
    * Formula: e_ij^X = p_i^X * omega_j^X
    * where:
    *   p_i^X = N_i^X / N_i  (source probability)
    *   omega_j^X = n_j^X / (sum_{k!=i} N_k^X)  (target interaction strength)
    
    qui {
        * The three groupings below are ordered so that only one of
        * them costs a re-sort. Tagging runs on
        * (year, feature, source, target); the subnet denominator groups
        * on (year, feature, source), a leading subset of that order, so
        * it reuses the sort; the node total groups on (year, source),
        * which is the single unavoidable re-sort and therefore comes
        * last.

        * Step 1: Tag one row per (year, feature, source)
        * The size is constant within that group but repeated for
        * each target, so without the tag each subnet would be counted
        * once per edge.
        tempvar _tfirst
        bysort year `feature' `nsrc' (`ntgt'): ///
            gen byte `_tfirst' = (_n == 1)

        * Step 2: Calculate sum_{k!=i} N_k^X
        * Within a source group the target entries are the quantity
        * measured at every node other than the source, so their sum
        * is the denominator. Reuses the sort from step 1.
        tempvar total_target_excl_source runtgt
        by year `feature' `nsrc': ///
            gen double `runtgt' = sum(`vtgt')
        by year `feature' `nsrc': ///
            gen double `total_target_excl_source' = `runtgt'[_N]
        drop `runtgt'

        * Step 3: Calculate N_i (total population in source node)
        * Running sum then last element, instead of egen total().
        * Stored as double, like the denominator above. The original
        * egen call left this one at the default float, whose integers
        * stop being exact above 16,777,216; a node total past that
        * silently rounded, and the error reached every weight through
        * p_source.
        tempvar total_source runsrc
        bysort year `nsrc': ///
            gen double `runsrc' = sum(`ssrc' * `_tfirst')
        by year `nsrc': gen double `total_source' = `runsrc'[_N]
        drop `runsrc'

        * Step 3b: Calculate p_i^X = N_i^X / N_i
        tempvar p_source
        gen double `p_source' = `ssrc' / `total_source'

        * Step 4: Calculate omega_j^X = n_j^X / sum_{k!=i} N_k^X
        tempvar omega_target
        gen double `omega_target' = `vtgt' ///
                                    / `total_target_excl_source'
        
        * Step 5: Calculate edge weight e_ij^X = p_i^X * omega_j^X
        tempvar edge_weight
        gen double `edge_weight' = `p_source' * `omega_target'

        * Nothing to take a share of is no share, not an undefined
        * one. A node that holds none of any subnet, and a subnet that
        * is absent from every node but the source, both weigh zero.
        replace `edge_weight' = 0 if `total_source' == 0 ///
                                   | `total_target_excl_source' == 0
        
        * Step 6: Create edge_id (source_target format)
        tempvar edge_id
        gen `edge_id' = source + "_" + target
        
        * Keep only necessary variables
        keep year `feature' source target `edge_id' `edge_weight'
        
        * Rename for output
        rename `edge_id' edge_id
        rename `edge_weight' edge_value
        rename `feature' feature
    }
    
    if "`debug'" != "" {
        di as text "_netcalc_interaction: Calculation completed"
        di as text "  Output observations: " _N
        sum edge_value, detail
    }
    
    * Return statistics
    sum edge_value, meanonly
    return scalar mean_weight = r(mean)
    return scalar n_edges = _N
    
end

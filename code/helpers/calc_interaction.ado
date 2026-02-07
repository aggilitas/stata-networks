*! calc_interaction v1.0.0
*! Helper function for calculating interaction network edge weights
*! Formula: e_ij^X = (N_i^X / N_i) * (n_j^X / sum_{k!=i} N_k^X)

program define calc_interaction, rclass
    version 16.0
    syntax, Feature(varname) Direction(string) [DEBUG]
    
    * Validate direction (for future use, currently not affecting interaction)
    if !inlist("`direction'", "outflow", "inflow") {
        di as error "direction() must be outflow or inflow"
        exit 198
    }
    
    * Validate required variables
    local required_vars year `feature' source target source_value target_value
    foreach var of local required_vars {
        capture confirm variable `var'
        if _rc {
            di as error "Variable `var' not found in dataset"
            exit 111
        }
    }
    
    if "`debug'" != "" {
        di as text "calc_interaction: Starting calculation"
        di as text "  Feature variable: `feature'"
        di as text "  Direction: `direction'"
        di as text "  Observations: " _N
    }
    
    * Preserve original data
    tempfile original
    qui save `original'
    
    * Calculate interaction network weights
    * Formula: e_ij^X = p_i^X * omega_j^X
    * where:
    *   p_i^X = N_i^X / N_i  (source probability)
    *   omega_j^X = n_j^X / (sum_{k!=i} N_k^X)  (target interaction strength)
    
    qui {
        * Step 1: Calculate N_i (total population in source node)
        * Sum all source_values for each (year, source) across all features
        tempvar total_source
        bysort year source: egen `total_source' = total(source_value)
        
        * Step 2: Calculate p_i^X = N_i^X / N_i
        tempvar p_source
        gen double `p_source' = source_value / `total_source'
        
        * Step 3: Calculate sum_{k!=i} N_k^X
        * For each (year, feature, target), sum all target_values EXCEPT from source node
        tempvar total_target_excl_source
        bysort year `feature' target: egen double `total_target_excl_source' = total(target_value)
        
        * Subtract the source node's contribution to target
        * (This is the target_value where target is in the source position)
        tempvar source_contrib
        gen `source_contrib' = .
        
        * For each observation, find the target_value when source and target are swapped
        * This is complex, so we'll use a different approach:
        * Total for feature in entire country minus source node's population of that feature
        
        tempvar total_feature_country
        bysort year `feature': egen double `total_feature_country' = total(target_value)
        
        * Subtract source node's population born in feature
        replace `total_target_excl_source' = `total_feature_country' - source_value
        
        * Step 4: Calculate omega_j^X = n_j^X / sum_{k!=i} N_k^X
        tempvar omega_target
        gen double `omega_target' = target_value / `total_target_excl_source'
        
        * Handle division by zero
        replace `omega_target' = 0 if missing(`omega_target')
        
        * Step 5: Calculate edge weight e_ij^X = p_i^X * omega_j^X
        tempvar edge_weight
        gen double `edge_weight' = `p_source' * `omega_target'
        
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
        di as text "calc_interaction: Calculation completed"
        di as text "  Output observations: " _N
        di as text "  Edge value range: " r(min) " to " r(max)
        sum edge_value, detail
    }
    
    * Return statistics
    sum edge_value, meanonly
    return scalar mean_weight = r(mean)
    return scalar n_edges = _N
    
end

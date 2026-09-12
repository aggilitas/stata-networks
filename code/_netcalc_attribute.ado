*! _netcalc_attribute 2.0.0
*! Helper function for calculating attribute network edge weights
*! Formula: w_ij = ln(A_j / A_i)

program define _netcalc_attribute, rclass
    version 16.0
    syntax, Subnet(string) [Feature(varname) DEBUG]
    
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
        local required_vars year `feature' source target ///
                            source_size source_value ///
                            target_size target_value
    }
    else {
        local required_vars year source target source_value target_value
    }
    
    foreach var of local required_vars {
        capture confirm variable `var'
        if _rc {
            di as error "Variable `var' not found in dataset"
            exit 111
        }
    }
    
    if "`debug'" != "" {
        di as text "_netcalc_attribute: Starting calculation"
        di as text "  Subnet: `subnet'"
        if "`subnet'" == "multi" {
            di as text "  Feature variable: `feature'"
        }
        di as text "  Observations: " _N
    }
    
    * Preserve original data
    tempfile original
    qui save `original'
    
    * Calculate attribute network weights
    * Formula: w_ij = ln(A_j / A_i). An inflow network is produced by
    * network_calc, which exchanges the node roles before calling this
    * routine, which is what flips the sign of the ratio.
    
    qui {
        tempvar edge_weight
        gen double `edge_weight' = ln(target_value / source_value)
        
        * Create edge_id (source_target format)
        tempvar edge_id
        gen `edge_id' = source + "_" + target
        
        * Keep only necessary variables
        if "`subnet'" == "multi" {
            keep year `feature' source target `edge_id' `edge_weight'
            rename `feature' feature
        }
        else {
            keep year source target `edge_id' `edge_weight'
        }
        
        * Rename for output
        rename `edge_id' edge_id
        rename `edge_weight' edge_value
        
        * Count missing values
        count if missing(edge_value)
        local n_missing = r(N)
        if `n_missing' > 0 {
            di as text "  Warning: `n_missing' edges have no" ///
                       " defined weight"
            di as text "  (likely due to zero or negative attribute values)"
        }
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
    qui count if !missing(edge_value)
    di as text "  Edges with a defined weight: " ///
       as result r(N) as text " of " as result _N
    return scalar n_valid = r(N)
    
end

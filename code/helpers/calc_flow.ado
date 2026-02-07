*! calc_flow v1.0.0
*! Helper function for calculating flow network edge weights
*! Formula: w_i = v_i / T(y,s) or T(y,f,s) for multi-subnet

program define calc_flow, rclass
    version 16.0
    syntax, Subnet(string) Direction(string) [Feature(varname) DEBUG]
    
    * Validate subnet type
    if !inlist("`subnet'", "single", "multi") {
        di as error "subnet() must be single or multi"
        exit 198
    }
    
    * Validate direction
    if !inlist("`direction'", "outflow", "inflow") {
        di as error "direction() must be outflow or inflow"
        exit 198
    }
    
    * For multi-subnet, feature is required
    if "`subnet'" == "multi" & "`feature'" == "" {
        di as error "feature() required for multi-subnet flow network"
        exit 198
    }
    
    * Validate required variables based on subnet type
    if "`subnet'" == "multi" {
        local required_vars year `feature' source target source_value target_value
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
        di as text "calc_flow: Starting calculation"
        di as text "  Subnet: `subnet'"
        di as text "  Direction: `direction'"
        if "`subnet'" == "multi" {
            di as text "  Feature variable: `feature'"
        }
        di as text "  Observations: " _N
    }
    
    * Preserve original data
    tempfile original
    qui save `original'
    
    * Calculate flow network weights
    * Formula: w_i = v_i / T(y,s)
    * where T(y,s) = sum of all values for same (year, source) or (year, feature, source)
    
    qui {
        * Select value variable based on direction
        if "`direction'" == "outflow" {
            local value_var source_value
        }
        else {
            local value_var target_value
        }
        
        * Calculate T(y,s) or T(y,f,s) - total for the group
        tempvar total_group
        if "`subnet'" == "multi" {
            * Group by year, feature, source
            bysort year `feature' source: egen double `total_group' = total(`value_var')
        }
        else {
            * Group by year, source
            bysort year source: egen double `total_group' = total(`value_var')
        }
        
        * Calculate edge weight w_i = v_i / T(y,s)
        tempvar edge_weight
        gen double `edge_weight' = `value_var' / `total_group'
        
        * Handle division by zero
        replace `edge_weight' = 0 if missing(`edge_weight')
        
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
    }
    
    if "`debug'" != "" {
        di as text "calc_flow: Calculation completed"
        di as text "  Output observations: " _N
        sum edge_value, detail
    }
    
    * Return statistics
    sum edge_value, meanonly
    return scalar mean_weight = r(mean)
    return scalar n_edges = _N
    
end

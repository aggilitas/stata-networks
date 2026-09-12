*! _netcalc_aggregate v1.0.0
*! Aggregates a multi-subnet network to single-subnet
*! Internal routine of network_calc; not for direct use

program define _netcalc_aggregate
    syntax , Networkname(string) [DEBUG]
    
    if "`debug'" != "" {
        di as text "_netcalc_frames: aggregate"
        di as text "  Network: `networkname'"
        di as text "  Aggregating from multi to single"
    }
    
    * Current data should be multi-subnet format
    * Check for feature variable
    capture confirm variable feature
    if _rc {
        di as error "Feature variable not found. Cannot aggregate."
        exit 111
    }
    
    * Check for required variables
    foreach var in year edge_id `networkname' {
        capture confirm variable `var'
        if _rc {
            di as error "Variable `var' not found. Cannot aggregate."
            exit 111
        }
    }
    
    * Save original multi data
    tempfile multidata
    qui save `multidata'
    
    * Aggregate by summing over features
    qui {
        collapse (sum) `networkname', by(year edge_id)
    }
    
    if "`debug'" != "" {
        di as text "  Aggregated to " _N " observations"
        sum `networkname', detail
    }
    
    * This aggregated data will be added to single frame by caller
end

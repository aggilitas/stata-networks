*! _netcalc_aggregate 2.0.0
*! Aggregates a multi-subnet network to single-subnet
*! Internal routine of network_calc; not for direct use

program define _netcalc_aggregate
    version 16.0
    syntax , Networkname(string) [DEBUG]
    
    if "`debug'" != "" {
        di as text "_netcalc_aggregate"
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
    
    * Aggregate by summing over features. source and target are
    * carried through the by() list rather than dropped: edge_id is
    * built from them, so they are constant within a group and the
    * grouping does not change, and the caller keeps the two node
    * columns to use as they see fit.
    qui {
        collapse (sum) `networkname', by(year edge_id source target)
    }
    
    if "`debug'" != "" {
        di as text "  Aggregated to " _N " observations"
        sum `networkname', detail
    }
    
    * This aggregated data will be added to single frame by caller
end

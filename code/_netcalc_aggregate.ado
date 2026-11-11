*! _netcalc_aggregate 2.2.0
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
    
    * Aggregate by summing over the levels of the feature. source
    * and target stand in the by() list beside edge_id: the label is
    * built from them, but two ordered pairs can share one label, and
    * the node columns are what keeps such pairs apart. The caller
    * also keeps the two node columns to use as they see fit.
    qui {
        collapse (sum) `networkname', by(year edge_id source target)

        * collapse labels what it sums, which would leave the reduced
        * copy of a network carrying a note that the same network
        * computed directly does not have
        label variable `networkname' ""
    }
    
    if "`debug'" != "" {
        di as text "  Aggregated to " _N " observations"
        sum `networkname', detail
    }
    
    * This aggregated data will be added to single frame by caller
end

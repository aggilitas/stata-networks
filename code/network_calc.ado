*! network_calc v1.0.0
*! Main command for calculating network edge weights
*! Author: Necmi TALAY
*! Date: 2026-02-07

program define network_calc, rclass
    version 16.0
    syntax, Type(string) ///
            Subnet(string) ///
            Name(string) ///
            [Feature(varname)] ///
            [Direction(string)] ///
            [DEBUG]
    
    *===========================================================================
    * 1. VALIDATE PARAMETERS
    *===========================================================================
    
    * Validate type
    if !inlist("`type'", "interaction", "flow", "attribute") {
        di as error "type() must be: interaction, flow, or attribute"
        exit 198
    }
    
    * Validate subnet
    if !inlist("`subnet'", "single", "multi") {
        di as error "subnet() must be: single or multi"
        exit 198
    }
    
    * Validate name
    if "`name'" == "" {
        di as error "name() is required"
        exit 198
    }
    
    * Check that name is valid Stata variable name
    capture confirm name `name'
    if _rc {
        di as error "name(`name') is not a valid Stata variable name"
        exit 198
    }
    
    * Set default direction
    if "`direction'" == "" {
        local direction "outflow"
    }
    
    * Validate direction
    if !inlist("`direction'", "outflow", "inflow") {
        di as error "direction() must be: outflow or inflow"
        exit 198
    }
    
    * Interaction network MUST be multi-subnet
    if "`type'" == "interaction" & "`subnet'" == "single" {
        di as error "Interaction networks must be multi-subnet"
        di as error "Please specify: subnet(multi) feature(varname)"
        exit 198
    }
    
    * Multi-subnet requires feature
    if "`subnet'" == "multi" & "`feature'" == "" {
        di as error "Multi-subnet networks require feature() option"
        exit 198
    }
    
    * Single-subnet should not have feature
    if "`subnet'" == "single" & "`feature'" != "" {
        di as text "Note: feature() ignored for single-subnet network"
        local feature ""
    }
    
    *===========================================================================
    * 2. DISPLAY HEADER
    *===========================================================================
    
    di ""
    di as text "{hline 78}"
    di as text "NETWORK_CALC: Calculating `type' network"
    di as text "{hline 78}"
    di as text "  Type:      " as result "`type'"
    di as text "  Subnet:    " as result "`subnet'"
    if "`subnet'" == "multi" {
        di as text "  Feature:   " as result "`feature'"
    }
    di as text "  Direction: " as result "`direction'"
    di as text "  Name:      " as result "`name'"
    di as text "  Obs:       " as result _N
    di as text "{hline 78}"
    
    *===========================================================================
    * 3. VALIDATE INPUT DATA
    *===========================================================================
    
    if "`debug'" != "" {
        di as text "Validating input data..."
    }
    
    * Check required variables based on subnet type
    if "`subnet'" == "multi" {
        local required_vars year `feature' source target source_value target_value
    }
    else {
        local required_vars year source target source_value target_value
    }
    
    foreach var of local required_vars {
        capture confirm variable `var'
        if _rc {
            di as error "Required variable `var' not found in dataset"
            di as error ""
            di as error "Expected format for `subnet'-subnet:"
            if "`subnet'" == "multi" {
                di as error "  year feature source target source_value target_value"
            }
            else {
                di as error "  year source target source_value target_value"
            }
            exit 111
        }
    }
    
    * Check for missing values in key variables
    local has_missing = 0
    foreach var of local required_vars {
        qui count if missing(`var')
        if r(N) > 0 {
            di as text "  Warning: `var' has " r(N) " missing values"
            local has_missing = 1
        }
    }
    
    if `has_missing' {
        di as text "  Observations with missing values will be dropped"
        qui drop if missing(year) | missing(source) | missing(target) | ///
                    missing(source_value) | missing(target_value)
        if "`subnet'" == "multi" {
            qui drop if missing(`feature')
        }
        di as text "  Remaining observations: " _N
    }
    
    *===========================================================================
    * 4. CALL APPROPRIATE CALCULATION FUNCTION
    *===========================================================================
    
    di as text ""
    di as text "Calculating network weights..."
    
    * Preserve original data
    tempfile original
    qui save `original'
    
    * Call calculation function based on type
    if "`type'" == "interaction" {
        calc_interaction, feature(`feature') direction(`direction') `debug'
    }
    else if "`type'" == "flow" {
        if "`subnet'" == "multi" {
            calc_flow, subnet(multi) direction(`direction') feature(`feature') `debug'
        }
        else {
            calc_flow, subnet(single) direction(`direction') `debug'
        }
    }
    else if "`type'" == "attribute" {
        if "`subnet'" == "multi" {
            calc_attribute, subnet(multi) direction(`direction') feature(`feature') `debug'
        }
        else {
            calc_attribute, subnet(single) direction(`direction') `debug'
        }
    }
    
    * Store calculation results
    local calc_n_edges = r(n_edges)
    local calc_mean_weight = r(mean_weight)
    
    di as text "  Calculated " as result `calc_n_edges' as text " edges"
    di as text "  Mean weight: " as result %9.6f `calc_mean_weight'
    
    *===========================================================================
    * 5. MANAGE FRAMES
    *===========================================================================
    
    di as text ""
    di as text "Managing network frames..."
    
    * Save calculated data
    tempfile calcdata
    qui save `calcdata'
    
    * Add to multi frame if multi-subnet
    if "`subnet'" == "multi" {
        di as text "  Adding to frame: networks_multi"
        use `calcdata', clear
        frame_manager create_or_join ///
            framename(networks_multi) ///
            networkname(`name') ///
            subnet(multi) ///
            `debug'
        
        * Aggregate to single
        di as text "  Aggregating to single-subnet..."
        use `calcdata', clear
        
        * Rename edge_value to network name before aggregating
        rename edge_value `name'
        
        frame_manager aggregate ///
            networkname(`name') `debug'
        
        * Save aggregated data
        tempfile aggdata
        qui save `aggdata'
        
        * Add aggregated to single frame
        di as text "  Adding aggregated to frame: networks_single"
        use `aggdata', clear
        frame_manager create_or_join ///
            framename(networks_single) ///
            networkname(`name') ///
            subnet(single) ///
            `debug'
    }
    else {
        * Single-subnet: just add to single frame
        di as text "  Adding to frame: networks_single"
        use `calcdata', clear
        frame_manager create_or_join ///
            framename(networks_single) ///
            networkname(`name') ///
            subnet(single) ///
            `debug'
    }
    
    * Restore original data
    use `original', clear
    
    *===========================================================================
    * 6. REPORT RESULTS
    *===========================================================================
    
    di as text ""
    di as text "{hline 78}"
    di as text "NETWORK_CALC: Completed successfully"
    di as text "{hline 78}"
    di as text "Network '`name'' has been calculated and added to:"
    
    if "`subnet'" == "multi" {
        frame networks_multi {
            local n_multi = _N
            qui describe, short
            local n_vars = r(k)
        }
        di as text "  - Frame 'networks_multi':  " as result %8.0f `n_multi' ///
           as text " obs, " as result `n_vars' as text " variables"
        
        frame networks_single {
            local n_single = _N
            qui describe, short
            local n_vars = r(k)
        }
        di as text "  - Frame 'networks_single': " as result %8.0f `n_single' ///
           as text " obs, " as result `n_vars' as text " variables (aggregated)"
    }
    else {
        frame networks_single {
            local n_single = _N
            qui describe, short
            local n_vars = r(k)
        }
        di as text "  - Frame 'networks_single': " as result %8.0f `n_single' ///
           as text " obs, " as result `n_vars' as text " variables"
    }
    
    di as text ""
    di as text "To view the networks:"
    di as text "  {stata frame change networks_single:frame change networks_single}"
    if "`subnet'" == "multi" {
        di as text "  {stata frame change networks_multi:frame change networks_multi}"
    }
    di as text "{hline 78}"
    di as text ""
    
    * Return values
    return scalar n_edges = `calc_n_edges'
    return scalar mean_weight = `calc_mean_weight'
    return local network_name "`name'"
    return local network_type "`type'"
    return local subnet_type "`subnet'"
    
end

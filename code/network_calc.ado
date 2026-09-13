*! network_calc 2.0.0
*! Main command for calculating network edge weights
*! Author: Necmi TALAY
*! Date: 2026-09-13

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
    
    * The output frames carry these five columns themselves, so a
    * network cannot be named after one of them.
    if inlist("`name'", "year", "source", "target", "edge_id", ///
                        "feature") {
        di as error "name(`name') is a reserved column name"
        di as error "year, source, target, edge_id and feature name" ///
                    " the frame itself"
        exit 198
    }

    * A name a frame already holds cannot be replaced: the merge
    * keeps the column the frame has and the newly computed weights
    * would be dropped without a word. Both frames are checked
    * whatever the call writes, and before anything is computed, so
    * that a name means one network wherever it appears and nothing
    * is half written.
    foreach fr in networks_single networks_multi {
        capture frame `fr': confirm variable `name'
        if _rc == 0 {
            di as error "`name' is already in frame `fr'"
            di as error "Drop it, or choose another name()"
            exit 110
        }
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
            di as error "Required variable `var' not found in dataset"
            di as error ""
            di as error "Expected format for `subnet'-subnet:"
            if "`subnet'" == "multi" {
                di as error "  year feature source target" ///
                            " source_size source_value" ///
                            " target_size target_value"
            }
            else {
                di as error "  year source target source_value target_value"
            }
            exit 111
        }
    }
    
    * A missing input has no place in any of this. Dropping the edge
    * would take it out of its denominator as well and the remaining
    * weights would still add up to one, over a mesh quietly missing
    * one of its alternatives; carrying it through leaves a missing
    * weight that the reduction to a single subnet would then sum
    * around. Neither is a network, so the command refuses the data.
    foreach var of local required_vars {
        qui count if missing(`var')
        if r(N) > 0 {
            di as error "`var' has " r(N) " missing values"
            exit 416
        }
    }
    
    *===========================================================================
    * 4. CALL APPROPRIATE CALCULATION FUNCTION
    *===========================================================================
    
    di as text ""
    di as text "Calculating network weights..."
    
    * Preserve original data
    tempfile original
    qui save `original'
    
    * Under subnet(multi) a weight is the share of the subnet in its
    * node multiplied by the network computed inside that subnet. A
    * size of zero is a subnet the node does not hold, which the
    * templates weigh as zero; a size below zero is not a size.
    if "`subnet'" == "multi" & "`type'" != "attribute" {
        local ssrc = cond("`direction'" == "inflow", ///
                          "target_size", "source_size")
        qui count if `ssrc' < 0
        if r(N) > 0 {
            di as error "subnet sizes can not be negative"
            exit 411
        }
    }

    * Call calculation function based on type
    if "`type'" == "interaction" {
        _netcalc_interaction, feature(`feature') ///
            direction(`direction') `debug'
    }
    else if "`type'" == "flow" {
        if "`subnet'" == "multi" {
            _netcalc_flow, subnet(multi) feature(`feature') ///
                direction(`direction') `debug'
        }
        else {
            _netcalc_flow, subnet(single) direction(`direction') `debug'
        }
    }
    else if "`type'" == "attribute" {
        if "`subnet'" == "multi" {
            _netcalc_attribute, subnet(multi) feature(`feature') ///
                direction(`direction') `debug'
        }
        else {
            _netcalc_attribute, subnet(single) ///
                direction(`direction') `debug'
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

        * A template that reduces to a single subnet leaves the share
        * of each subnet beside the weights: the raw size columns
        * turned into the ratio the subnet holds at its node. It is
        * written into the panel under the network's own name, so that
        * two networks can each carry their own: a call reads the size
        * columns of its own input, and two networks split the same
        * way need not weigh their subnets the same.
        capture confirm variable netcalc_fratio
        if _rc == 0 {
            qui rename netcalc_fratio `name'_fratio
        }

        _netcalc_join, ///
            framename(networks_multi) ///
            networkname(`name') ///
            subnet(multi) ///
            type(`type') ///
            `debug'
        
        * The single-subnet copy is the sum of the subnet weights.
        * That works where a subnet weight is a share: the shares of a
        * node add up over the subnets and the total is one. It does
        * not work for attribute, whose weight is a log ratio, so a sum
        * over subnets is a product of ratios and grows with their
        * number. An attribute network therefore stays in
        * networks_multi.
        if "`type'" == "attribute" {
            di as text "  Not aggregated to single-subnet: a log ratio"
            di as text "  does not add up over subnets. Pass the node"
            di as text "  level with subnet(single) for a single-subnet"
            di as text "  attribute network."
            local wrote_single = 0
        }
        else {
            di as text "  Aggregating to single-subnet..."
            use `calcdata', clear
            rename edge_value `name'

            * The weights of a subnet add up to one on their own, so
            * the copy is not their plain sum: each subnet enters it
            * scaled by the share the size columns give it, and the
            * shares of a node add up to one.
            capture confirm variable netcalc_fratio
            if _rc == 0 {
                qui replace `name' = `name' * netcalc_fratio
                qui drop netcalc_fratio
            }

            _netcalc_aggregate, ///
                networkname(`name') `debug'
            local wrote_single = 1
        }
        
        if `wrote_single' {
            tempfile aggdata
            qui save `aggdata'
            di as text "  Adding aggregated to frame: networks_single"
            use `aggdata', clear
            _netcalc_join, ///
                framename(networks_single) ///
                networkname(`name') ///
                subnet(single) ///
                type(`type') ///
                `debug'
        }
    }
    else {
        * Single-subnet: just add to single frame
        local wrote_single = 1
        di as text "  Adding to frame: networks_single"
        use `calcdata', clear
        _netcalc_join, ///
            framename(networks_single) ///
            networkname(`name') ///
            subnet(single) ///
            type(`type') ///
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
        
        if `wrote_single' {
            frame networks_single {
                local n_single = _N
                qui describe, short
                local n_vars = r(k)
            }
            di as text "  - Frame 'networks_single': " ///
               as result %8.0f `n_single' as text " obs, " ///
               as result `n_vars' as text " variables (aggregated)"
        }
    }
    else {
        frame networks_single {
            local n_single = _N
            qui describe, short
            local n_vars = r(k)
        }
        di as text "  - Frame 'networks_single': " ///
           as result %8.0f `n_single' as text " obs, " ///
           as result `n_vars' as text " variables"
    }
    
    di as text ""
    di as text "To view the networks:"
    if "`subnet'" != "multi" | `wrote_single' {
        di as text "  {stata frame change networks_single:" ///
                   "frame change networks_single}"
    }
    if "`subnet'" == "multi" {
        di as text "  {stata frame change networks_multi:" ///
                   "frame change networks_multi}"
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

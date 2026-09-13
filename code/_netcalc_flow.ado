*! _netcalc_flow 2.0.0
*! Helper function for calculating flow network edge weights
*! Formula: w_i = v_i / T(y,s) or T(y,f,s) for multi-subnet

program define _netcalc_flow, rclass
    version 16.0
    syntax, Subnet(string) Direction(string) ///
            [Feature(varname) DEBUG]
    
    * Validate subnet type
    if !inlist("`subnet'", "single", "multi") {
        di as error "subnet() must be single or multi"
        exit 198
    }
    
    * For multi-subnet, feature is required
    if "`subnet'" == "multi" & "`feature'" == "" {
        di as error "feature() required for multi-subnet flow network"
        exit 198
    }
    
    * Validate required variables based on subnet type
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
    
    * An inflow network is the same computation read from the other
    * end of the edge. Nothing in the data moves: the roles are
    * assigned to the other columns and the rest of the routine reads
    * through these names. The edge keeps its own orientation, so
    * edge_id is built from source and target as they stand.
    if "`direction'" == "inflow" {
        local nsrc target
        local ntgt source
        local vsrc target_value
        local ssrc target_size
    }
    else {
        local nsrc source
        local ntgt target
        local vsrc source_value
        local ssrc source_size
    }

    if "`debug'" != "" {
        di as text "_netcalc_flow: Starting calculation"
        di as text "  Subnet: `subnet'"
        if "`subnet'" == "multi" {
            di as text "  Feature variable: `feature'"
        }
        di as text "  Observations: " _N
    }
    
    * A flow can be zero, meaning nothing travelled along that edge,
    * but it cannot be negative. A negative value is a fault in the
    * data, and a share taken over a total that mixes signs would mean
    * nothing.
    qui count if `vsrc' < 0
    if r(N) > 0 {
        di as error "flows can not be negative"
        exit 411
    }
    
    * Calculate flow network weights
    * Formula: w_i = v_i / T(y,s)
    * where T(y,s) sums the values sharing (year, source), or
    * (year, feature, source) when the network has subnets
    
    tempvar netcalc_fratio

    qui {
        * The weight is the share of the edge in what leaves its
        * node. Under subnet(multi) that is read inside the subnet,
        * so the weights of a subnet add up to one on their own and
        * the subnet is a network in its own right.
        tempvar total_group runsum edge_weight
        if "`subnet'" == "multi" {
            bysort year `feature' `nsrc': ///
                gen double `runsum' = sum(`vsrc')
            by year `feature' `nsrc': ///
                gen double `total_group' = `runsum'[_N]
            drop `runsum'
            gen double `edge_weight' = `vsrc' / `total_group'
            replace `edge_weight' = 0 if `total_group' == 0

            * What size carries is the share of the subnet at the
            * node, and that is where the subnets are put back
            * together: the single-subnet copy adds up the subnet
            * weights after each has been scaled by its own share.
            * The column travels with the weights as far as the
            * reduction and no further.
            tempvar runsub total_sub runsize total_size
            bysort year `feature' `nsrc': ///
                gen double `runsub' = sum(`ssrc')
            by year `feature' `nsrc': ///
                gen double `total_sub' = `runsub'[_N]
            bysort year `nsrc': ///
                gen double `runsize' = sum(`ssrc')
            by year `nsrc': ///
                gen double `total_size' = `runsize'[_N]
            gen double `netcalc_fratio' = `total_sub' / `total_size'
            replace `netcalc_fratio' = 0 if `total_size' == 0
            drop `runsub' `total_sub' `runsize' `total_size'
        }
        else {
            bysort year `nsrc': ///
                gen double `runsum' = sum(`vsrc')
            by year `nsrc': gen double `total_group' = `runsum'[_N]
            drop `runsum'
            gen double `edge_weight' = `vsrc' / `total_group'

            * A node out of which nothing travels weighs zero.
            replace `edge_weight' = 0 if `total_group' == 0
        }
        
        * Create edge_id (source_target format)
        tempvar edge_id
        gen `edge_id' = source + "_" + target
        
        * Keep only necessary variables
        if "`subnet'" == "multi" {
            keep year `feature' source target `edge_id' ///
                 `edge_weight' `netcalc_fratio'
            rename `feature' feature
            rename `netcalc_fratio' netcalc_fratio
        }
        else {
            keep year source target `edge_id' `edge_weight'
        }
        
        * Rename for output
        rename `edge_id' edge_id
        rename `edge_weight' edge_value
        if "`subnet'" == "multi" {
            order year feature source target edge_id ///
                  netcalc_fratio edge_value
        }
        else {
            order year source target edge_id edge_value
        }
    }
    
    if "`debug'" != "" {
        di as text "_netcalc_flow: Calculation completed"
        di as text "  Output observations: " _N
        sum edge_value, detail
    }
    
    * Return statistics
    sum edge_value, meanonly
    return scalar mean_weight = r(mean)
    return scalar n_edges = _N
    
end

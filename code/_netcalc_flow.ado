*! _netcalc_flow 2.0.0
*! Helper function for calculating flow network edge weights
*! Formula: w_i = v_i / T(y,s) or T(y,f,s) for multi-subnet

program define _netcalc_flow, rclass
    version 16.0
    syntax, Subnet(string) [Feature(varname) DEBUG]
    
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
    
    if "`debug'" != "" {
        di as text "_netcalc_flow: Starting calculation"
        di as text "  Subnet: `subnet'"
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
    * where T(y,s) sums the values sharing (year, source), or
    * (year, feature, source) when the network has subnets
    
    qui {
        * Within a subnet the weight is the share of the edge in
        * what leaves its node. Across subnets that share is scaled by
        * the share of the subnet itself, which is what size carries,
        * so the weights of a node add up to one over subnets and
        * targets together, and the single-subnet copy is their sum.
        tempvar total_group runsum edge_weight
        if "`subnet'" == "multi" {
            bysort year `feature' source: ///
                gen double `runsum' = sum(source_value)
            by year `feature' source: ///
                gen double `total_group' = `runsum'[_N]
            drop `runsum'

            tempvar sfirst runsize total_size
            bysort year `feature' source (target): ///
                gen byte `sfirst' = (_n == 1)
            bysort year source: ///
                gen double `runsize' = sum(source_size * `sfirst')
            by year source: ///
                gen double `total_size' = `runsize'[_N]
            gen double `edge_weight' = (source_size / `total_size') ///
                                     * (source_value / `total_group')
            drop `runsize' `sfirst' `total_size'
        }
        else {
            bysort year source: ///
                gen double `runsum' = sum(source_value)
            by year source: gen double `total_group' = `runsum'[_N]
            drop `runsum'
            gen double `edge_weight' = source_value / `total_group'
        }
        
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
        di as text "_netcalc_flow: Calculation completed"
        di as text "  Output observations: " _N
        sum edge_value, detail
    }
    
    * Return statistics
    sum edge_value, meanonly
    return scalar mean_weight = r(mean)
    return scalar n_edges = _N
    
end

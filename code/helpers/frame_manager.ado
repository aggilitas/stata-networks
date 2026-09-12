*! frame_manager v1.0.0
*! Helper functions for managing network frames (create, join, aggregate)

program define frame_manager
    version 16.0
    
    * Parse subcommand
    gettoken subcmd 0 : 0 , parse(" ")
    
    if "`subcmd'" == "create_or_join" {
        create_or_join , `0'
    }
    else if "`subcmd'" == "aggregate" {
        aggregate_multi_to_single , `0'
    }
    else {
        di as error "Unknown frame_manager subcommand: `subcmd'"
        exit 198
    }
end

*===============================================================================
* SUBPROGRAM: create_or_join
* Purpose: Create new frame or join data to existing frame
*===============================================================================
program define create_or_join
    syntax , Framename(string) Networkname(string) Subnet(string) [DEBUG]
    
    * Validate subnet
    if !inlist("`subnet'", "single", "multi") {
        di as error "subnet() must be single or multi"
        exit 198
    }
    
    if "`debug'" != "" {
        di as text "frame_manager: create_or_join"
        di as text "  Frame: `framename'"
        di as text "  Network: `networkname'"
        di as text "  Subnet: `subnet'"
    }
    
    * Check if frame exists
    capture frame dir
    local frame_exists = 0
    if _rc == 0 {
        qui frame dir
        local all_frames `r(frames)'
        if strpos(" `all_frames' ", " `framename' ") > 0 {
            local frame_exists = 1
        }
    }
    
    * Temp file for current data
    tempfile newdata
    qui save `newdata'
    
    if `frame_exists' == 0 {
        * CREATE: Frame doesn't exist, create it
        if "`debug'" != "" {
            di as text "  Creating new frame: `framename'"
        }
        
        frame create `framename'
        frame `framename' {
            use `newdata', clear
            
            * Rename edge_value to network name if it exists
            capture confirm variable edge_value
            if _rc == 0 {
                rename edge_value `networkname'
            }
            * Otherwise, data already has the network name (from aggregation)
        }
    }
    else {
        * JOIN: Frame exists, merge new network
        if "`debug'" != "" {
            di as text "  Joining to existing frame: `framename'"
        }
        
        * Rename edge_value to network name before merging (if it exists)
        capture confirm variable edge_value
        if _rc == 0 {
            qui rename edge_value `networkname'
        }
        * Otherwise, data already has the network name (from aggregation)
        
        * Save modified data
        qui save `newdata', replace
        
        * Merge with existing frame
        frame `framename' {
            tempfile framedata
            qui save `framedata'
            
            * Determine merge keys
            if "`subnet'" == "multi" {
                local merge_keys year feature edge_id
            }
            else {
                local merge_keys year edge_id
            }
            
            * Merge
            qui merge 1:1 `merge_keys' using `newdata', nogenerate
            
            * Check for missing values in key variables
            foreach key of local merge_keys {
                count if missing(`key')
                if r(N) > 0 {
                    di as error "  Error: Missing values in merge key `key'"
                }
            }
            
            * Verify merge was successful
            count if missing(`networkname')
            if r(N) > 0 & r(N) < _N {
                di as text "  Warning: `networkname' has missing values in " r(N) " observations"
                di as text "  This may indicate edge mismatch between networks"
            }
        }
    }
    
    if "`debug'" != "" {
        frame `framename': di as text "  Frame `framename' now has " _N " observations"
        frame `framename': describe, short
    }
end

*===============================================================================
* SUBPROGRAM: aggregate_multi_to_single
* Purpose: Aggregate multi-subnet network to single-subnet by summing over features
*===============================================================================
program define aggregate_multi_to_single
    syntax , Networkname(string) [DEBUG]
    
    if "`debug'" != "" {
        di as text "frame_manager: aggregate"
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

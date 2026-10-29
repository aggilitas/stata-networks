*! _netcalc_join 2.1.0
*! Creates a network frame or joins a network with the same rows to it
*! Internal routine of network_calc; not for direct use

program define _netcalc_join
    version 16.0
    syntax , Framename(string) Networkname(string) Subnet(string) ///
              Type(string) [DEBUG]
    
    * Validate subnet
    if !inlist("`subnet'", "single", "multi") {
        di as error "subnet() must be single or multi"
        exit 198
    }
    
    if "`debug'" != "" {
        di as text "_netcalc_join"
        di as text "  Frame: `framename'"
        di as text "  Network: `networkname'"
        di as text "  Subnet: `subnet'"
    }
    
    * Ask the frame itself rather than listing every frame and
    * searching the list for its name.
    capture frame `framename': qui describe
    local frame_exists = (_rc == 0)
    
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

            * Record the template the column came from.
            char `networkname'[netcalc_type] "`type'"
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
            * Determine merge keys
            if "`subnet'" == "multi" {
                local merge_keys year feature edge_id
            }
            else {
                local merge_keys year edge_id
            }
            
            * Every network in a frame is a column of the same edge
            * panel. network_calc has checked, before any frame was
            * written, that the call brings exactly the rows the frame
            * holds, so every row matches and nothing is filled in on
            * either side.
            qui merge 1:1 `merge_keys' using `newdata', assert(match)
            qui drop _merge

            char `networkname'[netcalc_type] "`type'"
        }
    }
    
    if "`debug'" != "" {
        frame `framename': di as text ///
            "  Frame `framename' now has " _N " observations"
        frame `framename': describe, short
    }
end


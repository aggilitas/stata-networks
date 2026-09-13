*! _netcalc_join 2.0.0
*! Creates a network frame or joins a network to it
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

            * Record the template the column came from. A later join
            * needs it to know whether an edge the column does not
            * reach weighs zero or is unknown.
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
            * panel, so the frame is only a panel while the networks
            * agree on the edges. The merge keeps the union, which
            * means the network computed first sets the skeleton and
            * anything the later one adds arrives with the earlier
            * columns empty. Report both sides of the difference
            * rather than let it pass as a successful call.
            qui merge 1:1 `merge_keys' using `newdata'
            qui count if _merge == 3
            local n_both = r(N)
            qui count if _merge == 1
            local n_frame = r(N)
            qui count if _merge == 2
            local n_new = r(N)

            char `networkname'[netcalc_type] "`type'"

            * An edge a network does not reach is not a gap in that
            * network: the weight there is zero. For interaction and
            * flow the total the weights were divided by never counted
            * that edge, so nothing already in the frame moves. An
            * attribute weight is a log ratio and is part of no total
            * at all; an edge the network does not reach holds no
            * value at either end, so the two carry no difference and
            * the log of their ratio is zero.
            *
            * Only the rows the merge itself introduced are filled,
            * and only the columns network_calc wrote, which is what
            * the characteristic marks.
            if `n_frame' > 0 {
                qui replace `networkname' = 0 if _merge == 1
            }
            if `n_new' > 0 {
                qui ds
                local allvars `r(varlist)'
                foreach v of local allvars {
                    if "`v'" == "`networkname'" continue
                    local vtype : char `v'[netcalc_type]
                    if "`vtype'" != "" {
                        qui replace `v' = 0 if _merge == 2
                    }
                }
            }
            qui drop _merge

            if `n_both' == 0 {
                di as error "  `networkname' shares no edge with the" ///
                            " networks already in `framename'"
            }
            if `n_frame' > 0 | `n_new' > 0 {
                di as text "  Note: the networks in `framename' do not" ///
                           " cover the same edges"
                di as text "    matched:        " as result %8.0f `n_both'
                di as text "    only in frame:  " as result %8.0f `n_frame'
                di as text "    only in new:    " as result %8.0f `n_new'
                di as text "  A network weighs zero on the edges it" ///
                           " does not reach."
            }
        }
    }
    
    if "`debug'" != "" {
        frame `framename': di as text ///
            "  Frame `framename' now has " _N " observations"
        frame `framename': describe, short
    }
end


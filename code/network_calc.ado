*! network_calc 2.1.0
*! Main command for calculating network edge weights
*! Author: Necmi TALAY
*! Date: 2026-10-27

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

    * Option values ignore case and may be shortened to any unambiguous
    * leading part, so type(Flow), type(f) and direction(IN) name values
    * the command knows.
    _netcalc_pick `"`type'"' "interaction flow attribute"
    local type `r(pick)'
    if "`type'" == "" {
        di as error "type() must be: interaction, flow, or attribute"
        exit 198
    }

    _netcalc_pick `"`subnet'"' "single multi"
    local subnet `r(pick)'
    if "`subnet'" == "" {
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
    if `"`direction'"' == "" {
        local direction "outflow"
    }

    _netcalc_pick `"`direction'"' "outflow inflow"
    local direction `r(pick)'
    if "`direction'" == "" {
        di as error "direction() must be: outflow or inflow"
        exit 198
    }

    * Interaction network MUST be multi-subnet
    if "`type'" == "interaction" & "`subnet'" == "single" {
        di as error "Interaction networks must be multi-subnet"
        di as error "Please specify: subnet(multi) feature(varname)"
        exit 198
    }

    * An attribute describes the node, so it has no subnets: the node
    * level is computed before the call and passed with subnet(single).
    if "`type'" == "attribute" & "`subnet'" == "multi" {
        di as error "Attribute networks have no subnets"
        di as error "An attribute describes the node; pass the node" ///
                    " level with subnet(single)"
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

    * The templates hand the ratio column over as netcalc_fratio and
    * the join marks the rows of its merge in _merge, so a network
    * cannot take either name.
    if inlist("`name'", "netcalc_fratio", "_merge") {
        di as error "name(`name') is used by network_calc itself"
        exit 198
    }

    * A multi-subnet call writes a second column, the name with
    * _fratio added. A variable name holds at most 32 characters,
    * which leaves 25 for the network.
    if "`subnet'" == "multi" & ustrlen("`name'") > 25 {
        di as error "name(`name') is longer than 25 characters"
        di as error "subnet(multi) adds _fratio to it for a second column"
        exit 198
    }

    * A name a frame already holds cannot be replaced: the merge
    * keeps the column the frame has and the newly computed weights
    * would be dropped without a word. Both frames are checked
    * whatever the call writes, and before anything is computed, so
    * that a name means one network wherever it appears and nothing
    * is half written. The ratio column a name would bring is
    * checked the same way.
    foreach fr in networks_single networks_multi {
        capture frame `fr': confirm variable `name'
        if _rc == 0 {
            di as error "`name' is already in frame `fr'"
            di as error "Drop it, or choose another name()"
            exit 110
        }
        capture frame `fr': confirm variable `name'_fratio
        if _rc == 0 {
            di as error "`name'_fratio is already in frame `fr'"
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

    * The data in memory is given back as it was found, down to
    * whether it has changed since it was read and the file it came
    * from. Saving it to a temporary file and reading that back would
    * have set both to the temporary file. From here on the data can
    * be sorted and cut freely, and a refusal gives it back as well.
    preserve

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

    * edge_id joins source and target with an underscore, so both
    * must be strings and neither may hold an underscore of its own:
    * a_b with c and a with b_c would both become a_b_c.
    foreach var in source target {
        capture confirm string variable `var'
        if _rc {
            di as error "`var' must be a string variable"
            exit 459
        }
        qui count if strpos(`var', "_") > 0
        if r(N) > 0 {
            di as error "`var' holds an underscore in " r(N) ///
                        " observations"
            di as error "edge_id joins source and target with one"
            exit 459
        }
    }

    * The source is not one of its own alternatives: every total of
    * the templates runs over k != i, and a self-loop would sit inside
    * one without showing in the row sums.
    qui count if source == target
    if r(N) > 0 {
        di as error "source and target are the same node in " r(N) ///
                    " observations"
        di as error "a node is not one of its own alternatives"
        exit 459
    }

    * An edge appears once in a period, and once in each subnet under
    * subnet(multi). A second copy would sit inside its own
    * denominator and the frames, which are keyed on the edge, could
    * not hold both.
    local key year `feature' source target
    local key : list retokenize key
    capture isid `key'
    if _rc {
        di as error "`key' do not identify the observations"
        di as error "an edge appears more than once in a period"
        exit 459
    }

    *===========================================================================
    * 4. CALL APPROPRIATE CALCULATION FUNCTION
    *===========================================================================

    di as text ""
    di as text "Calculating network weights..."

    * Under subnet(multi) a weight is computed inside its subnet, and
    * the ratio of the subnet within the feature at its node enters
    * only where the subnets are put back together. A size of zero is
    * a subnet the node does not hold, which the templates weigh as
    * zero; a size below zero is not a size.
    if "`subnet'" == "multi" {
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
        _netcalc_attribute, direction(`direction') `debug'
    }

    * Store calculation results
    local calc_n_edges = r(n_edges)
    local calc_mean_weight = r(mean_weight)

    * Under subnet(multi) a row is an edge of one subnet, so the rows
    * outnumber the ordered pairs; both counts are reported.
    tempvar firstpair
    qui bysort year edge_id: gen byte `firstpair' = _n == 1
    qui count if `firstpair'
    local calc_n_pairs = r(N)
    drop `firstpair'

    if "`subnet'" == "multi" {
        di as text "  Calculated " as result `calc_n_edges' ///
           as text " subnet-edge rows (" as result `calc_n_pairs' ///
           as text " edges)"
    }
    else {
        di as text "  Calculated " as result `calc_n_edges' as text " edges"
    }
    di as text "  Mean weight: " as result %9.6f `calc_mean_weight'

    *===========================================================================
    * 5. CHECK EVERY FRAME BEFORE WRITING ANY
    *===========================================================================

    * Whatever could stop a join is checked here, against every frame
    * the call writes, before the first of them changes, so that a
    * call writes both frames or neither.
    *
    * An attribute describes the node, as population or output
    * describe a province, so a node is never without it and an
    * attribute column holds a value on every edge of its frame. A
    * weight can be zero on an edge that exists, as the flows of a
    * city are on a day of curfew, and the join writes that zero; an
    * attribute cannot, so the join refuses instead. An attribute
    * network must reach every edge its frame holds, and a frame that
    * holds an attribute column takes no edge the column lacks.

    tempname NEWE FRE
    if "`subnet'" == "multi" {
        local frames_to_write networks_multi networks_single
    }
    else {
        local frames_to_write networks_single
    }

    foreach fr of local frames_to_write {
        local tag = cond("`fr'" == "networks_multi", "multi", "single")
        local keys = cond("`tag'" == "multi", ///
                          "year feature edge_id", "year edge_id")
        local n_both_`tag' = 0
        local n_frame_`tag' = 0

        * the edges this call brings to the frame
        capture frame drop `NEWE'
        frame put `keys', into(`NEWE')
        frame `NEWE' {
            qui duplicates drop
            local n_new_`tag' = _N
        }

        capture frame `fr': describe, short
        if _rc {
            continue
        }

        * the key must join: present in the frame, and string or
        * numeric on both sides alike
        foreach k of local keys {
            capture frame `fr': confirm variable `k', exact
            if _rc {
                di as error "frame `fr' has no variable `k' to join on"
                di as error "Nothing has been written"
                exit 459
            }
            capture confirm string variable `k'
            local new_str = (_rc == 0)
            capture frame `fr': confirm string variable `k'
            local old_str = (_rc == 0)
            if `new_str' != `old_str' {
                di as error "`k' is " ///
                    cond(`new_str', "string", "numeric") ///
                    " in the data and " ///
                    cond(`old_str', "string", "numeric") ///
                    " in frame `fr'"
                di as error "Nothing has been written"
                exit 106
            }
        }

        * whether the frame already holds an attribute column
        local frame_attr = 0
        frame `fr' {
            qui ds
            foreach v in `r(varlist)' {
                local vt : char `v'[netcalc_type]
                if "`vt'" == "attribute" {
                    local frame_attr = 1
                }
            }
        }

        * the edges found on one side only
        capture frame drop `FRE'
        frame copy `fr' `FRE'
        frame `FRE' {
            keep `keys'
            qui frlink 1:1 `keys', frame(`NEWE') ///
                generate(_netcalc_link)
            qui count if missing(_netcalc_link)
            local n_frame_`tag' = r(N)
        }
        frame `NEWE' {
            qui frlink 1:1 `keys', frame(`FRE') ///
                generate(_netcalc_link)
            qui count if missing(_netcalc_link)
            local n_only = r(N)
        }
        local n_both_`tag' = `n_new_`tag'' - `n_only'
        local n_new_`tag' = `n_only'
        capture frame drop `FRE'

        if "`type'" == "attribute" & `n_frame_`tag'' > 0 {
            di as error "`name' does not reach " `n_frame_`tag'' ///
                        " edges that frame `fr' holds"
            di as error "An attribute describes the node and cannot be" ///
                        " absent on an edge;"
            di as error "build it on every edge of the frame." ///
                        " Nothing has been written"
            exit 459
        }
        if `frame_attr' & `n_new_`tag'' > 0 {
            di as error "`name' brings " `n_new_`tag'' ///
                        " edges that frame `fr' does not hold"
            di as error "The frame holds an attribute column, which" ///
                        " cannot be absent on an edge."
            di as error "Nothing has been written"
            exit 459
        }
    }
    capture frame drop `NEWE'

    *===========================================================================
    * 6. MANAGE FRAMES
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

        * A template that reduces to a single subnet leaves the ratio
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

        * The single-subnet copy adds the subnet weights up after
        * each has been scaled by the ratio its subnet holds at the
        * node. A subnet weight is a share of what leaves the node, in
        * flow and interaction alike, and the ratios of a node add up
        * to one, so the copy is a weight again.
        di as text "  Aggregating to single-subnet..."
        use `calcdata', clear
        rename edge_value `name'

        capture confirm variable netcalc_fratio
        if _rc == 0 {
            qui replace `name' = `name' * netcalc_fratio
            qui drop netcalc_fratio
        }

        _netcalc_aggregate, ///
            networkname(`name') `debug'

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
    else {
        * Single-subnet: just add to single frame
        di as text "  Adding to frame: networks_single"
        use `calcdata', clear
        _netcalc_join, ///
            framename(networks_single) ///
            networkname(`name') ///
            subnet(single) ///
            type(`type') ///
            `debug'
    }

    * Give the data in memory back as it was found
    restore

    *===========================================================================
    * 7. REPORT RESULTS
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
        di as text "  - Frame 'networks_single': " ///
           as result %8.0f `n_single' as text " obs, " ///
           as result `n_vars' as text " variables (aggregated)"
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
    di as text "  {stata frame change networks_single:" ///
               "frame change networks_single}"
    if "`subnet'" == "multi" {
        di as text "  {stata frame change networks_multi:" ///
                   "frame change networks_multi}"
    }
    di as text "{hline 78}"
    di as text ""

    * Return values
    return scalar n_edges = `calc_n_edges'
    return scalar n_pairs = `calc_n_pairs'
    return scalar mean_weight = `calc_mean_weight'
    foreach tag in single multi {
        if "`n_new_`tag''" != "" {
            return scalar matched_`tag' = `n_both_`tag''
            return scalar frame_only_`tag' = `n_frame_`tag''
            return scalar new_only_`tag' = `n_new_`tag''
        }
    }
    return local network_name "`name'"
    return local network_type "`type'"
    return local subnet_type "`subnet'"

end


* Match an option value against the words it may take, ignoring case
* and accepting any unambiguous leading part. An empty value, or one
* that matches no word or more than one, returns nothing.
program define _netcalc_pick, rclass
    version 16.0
    args value words
    local value = lower(strtrim(`"`value'"'))
    local hit
    local n = 0
    if `"`value'"' != "" {
        foreach w of local words {
            if strpos("`w'", `"`value'"') == 1 {
                local hit `w'
                local ++n
            }
        }
    }
    if `n' != 1 {
        local hit
    }
    return local pick `hit'
end

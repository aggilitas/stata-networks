*! network_calc 2.2.0
*! Main command for calculating network edge weights
*! Author: Necmi TALAY
*! Date: 2026-11-03

program define network_calc, rclass
    version 16.0
    syntax, Type(string) ///
            Subnet(string) ///
            Name(string) ///
            [Feature(varname) ///
             Direction(string) ///
             PERiod(varname) ///
             SOurce(varname) ///
             TArget(varname) ///
             Value(varlist min=2 max=2) ///
             SIze(varlist min=2 max=2) ///
             REPLACE ///
             DEBUG]

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

    * nor size columns: a single-subnet call reads none
    if "`subnet'" == "single" & "`size'" != "" {
        di as text "Note: size() ignored for single-subnet network"
        local size ""
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

    * A name a frame already holds is not written over without a
    * word: the merge would keep the column the frame has and drop the
    * newly computed weights. Both frames are checked whatever the
    * call writes, and before anything is computed, so that a name
    * means one network wherever it appears and nothing is half
    * written. The ratio column a name would bring is checked the same
    * way. The check is exact: a name that only abbreviates a variable
    * in a frame is a new name. With replace, the columns found are
    * noted here and dropped from both frames once every check has
    * passed, so a refused call leaves the old network in place.
    local held
    foreach fr in networks_single networks_multi {
        foreach v in `name' `name'_fratio {
            capture frame `fr': confirm variable `v', exact
            if _rc == 0 {
                if "`replace'" == "" {
                    di as error "`v' is already in frame `fr'"
                    di as error "Drop it, choose another name()," ///
                                " or specify replace"
                    exit 110
                }
                local held `held' `fr'.`v'
            }
        }
    }

    *---------------------------------------------------------------------------
    * The variables the command reads, under the names the data give
    * them. Each role has a default name, which is also the name the
    * output frames carry; an option names another variable for it.
    *---------------------------------------------------------------------------

    if "`period'" == "" {
        local period year
    }
    if "`source'" == "" {
        local source source
    }
    if "`target'" == "" {
        local target target
    }
    if "`value'" == "" {
        local value source_value target_value
    }
    if "`size'" == "" {
        local size source_size target_size
    }
    local roles year source target source_value target_value
    local given `period' `source' `target' `value'
    if "`subnet'" == "multi" {
        local roles `roles' source_size target_size
        local given `given' `size'
    }

    local nroles : word count `roles'
    forvalues k = 1/`nroles' {
        local role : word `k' of `roles'
        local var : word `k' of `given'
        capture confirm variable `var', exact
        if _rc {
            if "`var'" == "`role'" {
                di as error "Required variable `role' not found in dataset"
            }
            else {
                di as error "`var', named for `role', not found in dataset"
            }
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
            di as error "or the variables named in period(), source()," ///
                        " target(), value() and size()"
            exit 111
        }
    }

    * one variable fills one role
    local dup : list dups given
    if "`dup'" != "" {
        di as error "`dup' is named for more than one of: `roles'"
        exit 198
    }
    if "`feature'" != "" {
        if `: list feature in given' {
            di as error "`feature' cannot be both the feature and one of:" ///
                        " `roles'"
            exit 198
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
    if "`given'" != "`roles'" {
        local readas
        forvalues k = 1/`nroles' {
            local role : word `k' of `roles'
            local var : word `k' of `given'
            if "`var'" != "`role'" {
                local readas `readas' `var'=`role'
            }
        }
        di as text "  Read as:   " as result "`readas'"
    }
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

    * From here on the command reads its variables under its own
    * names, which are also the names the output frames carry; the
    * refusals below list the rows under those names.
    _netcalc_adopt, roles(`roles') given(`given')
    capture drop edge_id

    local required_vars `roles'

    * The key of an observation: the period, the subnet under
    * subnet(multi), and the ordered pair.
    local key year `feature' source target
    local key : list retokenize key

    * A missing input has no place in any of this. Dropping the edge
    * would take it out of its denominator as well and the remaining
    * weights would still add up to one, over a mesh quietly missing
    * one of its alternatives; carrying it through leaves a missing
    * weight that the reduction to a single subnet would then sum
    * around. Neither is a network, so the command refuses the data
    * and lists the rows.
    foreach var of local required_vars {
        qui count if missing(`var')
        if r(N) > 0 {
            di as error "`var' has " r(N) " missing values, in these rows:"
            local show : list key | var
            _netcalc_show if missing(`var'), vars(`show')
            di as error "Nothing has been written"
            exit 416
        }
    }

    * The two ends of an edge name nodes of one kind: both string or
    * both numeric, so that a name at one end can be looked for at the
    * other. Either kind is accepted; edge_id is built from the values.
    capture confirm string variable source
    local s_str = (_rc == 0)
    capture confirm string variable target
    local t_str = (_rc == 0)
    if `s_str' != `t_str' {
        di as error "source is " cond(`s_str', "string", "numeric") ///
                    " and target is " cond(`t_str', "string", "numeric")
        di as error "both must be of one kind. Nothing has been written"
        exit 459
    }

    * The source is not one of its own alternatives: every total of
    * the templates runs over k != i, and a self-loop would sit inside
    * one without showing in the row sums.
    qui count if source == target
    if r(N) > 0 {
        di as error "source and target are the same node in " r(N) ///
                    " observations:"
        _netcalc_show if source == target, vars(`key')
        di as error "a node is not one of its own alternatives." ///
                    " Nothing has been written"
        exit 459
    }

    * An edge appears once in a period, and once in each subnet under
    * subnet(multi). A second copy would sit inside its own
    * denominator and the frames, which are keyed on the edge, could
    * not hold both.
    capture isid `key'
    if _rc {
        tempvar dup
        qui duplicates tag `key', generate(`dup')
        qui count if `dup' > 0
        di as error "`key' do not identify the observations:" ///
                    " these " r(N) " rows share their key"
        sort `key'
        _netcalc_show if `dup' > 0, vars(`key')
        di as error "an edge appears more than once in a period." ///
                    " Nothing has been written"
        exit 459
    }

    * Every row the panel can have must be there: each period, each
    * level of the feature under subnet(multi), and each ordered pair
    * of distinct nodes, the nodes being every name the data give as
    * source or target. A pair with nothing to record is a row with
    * zero, and the data supply it; the command fills in no row and no
    * value. A row the data lack therefore stops it, and the rows are
    * listed.
    if "`feature'" != "" {
        _netcalc_mesh, feature(`feature')
    }
    else {
        _netcalc_mesh
    }

    * A figure that describes a node is repeated on every row that
    * names the node, and the rows must agree: under interaction the
    * size and the value of a subnet at its node, under attribute the
    * level of the node. A row that carries another figure is a slip
    * in the layout, which the weights would carry without a word, so
    * the data are refused and the nodes listed. Under flow the values
    * describe the edge and the sizes may, so nothing is repeated.
    if "`type'" == "interaction" {
        _netcalc_constant, stem(size) feature(`feature')
        _netcalc_constant, stem(value) feature(`feature')
    }
    else if "`type'" == "attribute" {
        _netcalc_constant, stem(value)
    }

    * The label of the ordered pair, carried into the frames beside
    * the two node columns: the values of source and target joined by
    * an underscore. The frames are keyed on the node columns, so the
    * label need not be unambiguous and the names may hold what they
    * like.
    _netcalc_edgeid

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
    local calc_zero_totals = r(n_zero_totals)
    local calc_zero_sizes = r(n_zero_sizes)

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

    * A total of zero is not refused: a node out of which nothing
    * travels, or a subnet with nothing outside the source, has its
    * weights written as zero. It is said here, so that it does not
    * pass without a word, and returned in r().
    if `calc_zero_totals' > 0 {
        local unit = cond("`subnet'" == "multi", ///
                          "node-period-subnet", "node-period")
        di as text "  Note: " as result `calc_zero_totals' as text ///
           " `unit' totals are zero; the weights read over them" ///
           " are written as zero"
    }
    if `calc_zero_sizes' > 0 {
        di as text "  Note: " as result `calc_zero_sizes' as text ///
           " node-period size totals are zero; the ratios of those" ///
           " nodes are written as zero"
    }

    *===========================================================================
    * 5. CHECK EVERY FRAME BEFORE WRITING ANY
    *===========================================================================

    * Whatever could stop a join is checked here, against every frame
    * the call writes, before the first of them changes, so that a
    * call writes both frames or neither.
    *
    * A frame is a panel of edges and every network in it is a column
    * of that panel, so a network joins a frame only with the rows the
    * frame holds: the same periods, the same edges and, in
    * networks_multi, the same subnets. Nothing is filled in on either
    * side. A call with a row the frame lacks, or without a row the
    * frame holds, is refused, and the rows are listed.

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
                          "year feature source target", ///
                          "year source target")

        * the edges this call brings to the frame
        capture frame drop `NEWE'
        frame put `keys', into(`NEWE')
        frame `NEWE' {
            qui duplicates drop
        }

        capture frame `fr': describe, short
        if _rc {
            continue
        }

        * the join records its matches in _merge, so the frame must
        * not hold a variable of that name
        capture frame `fr': confirm variable _merge, exact
        if _rc == 0 {
            di as error "frame `fr' holds a variable named _merge," ///
                        " which the join uses"
            di as error "Drop or rename it. Nothing has been written"
            exit 110
        }

        * networks_multi is split by one feature. The frame records
        * the name of the variable, and a call that names another
        * variable in feature() is refused, also where the levels of
        * the two coincide: two files that name the same feature
        * differently are brought to one name before the call.
        if "`tag'" == "multi" {
            frame `fr' {
                local split : char feature[netcalc_feature]
            }
            if "`split'" != "" & "`split'" != "`feature'" {
                di as error "frame `fr' is split by `split'," ///
                            " not by `feature'"
                di as error "Nothing has been written"
                exit 459
            }
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

        * the rows found on one side only
        capture frame drop `FRE'
        frame `fr': frame put `keys', into(`FRE')
        frame `FRE' {
            qui frlink 1:1 `keys', frame(`NEWE') ///
                generate(_netcalc_link)
            qui count if missing(_netcalc_link)
            local n_lack = r(N)
        }
        frame `NEWE' {
            qui frlink 1:1 `keys', frame(`FRE') ///
                generate(_netcalc_link)
            qui count if missing(_netcalc_link)
            local n_more = r(N)
        }

        if `n_lack' > 0 | `n_more' > 0 {
            di as error "`name' does not have the rows of frame `fr'"
            if `n_lack' > 0 {
                di as error "  " `n_lack' " rows of the frame that" ///
                            " `name' lacks:"
                frame `FRE' {
                    sort `keys'
                    _netcalc_show if missing(_netcalc_link), vars(`keys')
                }
            }
            if `n_more' > 0 {
                di as error "  " `n_more' " rows of `name' that the" ///
                            " frame lacks:"
                frame `NEWE' {
                    sort `keys'
                    _netcalc_show if missing(_netcalc_link), vars(`keys')
                }
            }
            di as error "Every network in a frame has the rows of the" ///
                        " frame. Nothing has been written"
            capture frame drop `FRE'
            capture frame drop `NEWE'
            exit 459
        }
        capture frame drop `FRE'
    }
    capture frame drop `NEWE'

    *===========================================================================
    * 6. MANAGE FRAMES
    *===========================================================================

    di as text ""
    di as text "Managing network frames..."

    * With replace, the name is cleared from both frames, the ratio
    * column with it, now that every check has passed and the call is
    * going to be written.
    foreach item of local held {
        local fr = substr("`item'", 1, strpos("`item'", ".") - 1)
        local v = substr("`item'", strpos("`item'", ".") + 1, .)
        di as text "  Replacing `v' in frame `fr'"
        frame `fr': drop `v'
    }

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
            featurename(`feature') ///
            `debug'

        * The single-subnet copy adds the subnet weights up after
        * each has been scaled by the ratio its subnet holds at the
        * node. A subnet weight is a part of what leaves the node, in
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
    return scalar n_zero_totals = `calc_zero_totals'
    return scalar n_zero_sizes = `calc_zero_sizes'
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


* Give each role its variable under the command's own name. The
* variables named for the roles are moved to temporary names first,
* so that two of them may change places, a column that only bears a
* role's name is dropped as being in the way, and each temporary name
* then takes the name of its role. The data in memory are under
* preserve, so nothing of this reaches the user.
program define _netcalc_adopt
    version 16.0
    syntax, Roles(string) Given(string)
    local n : word count `roles'
    forvalues k = 1/`n' {
        local var : word `k' of `given'
        tempvar t`k'
        rename `var' `t`k''
    }
    foreach role of local roles {
        capture confirm variable `role', exact
        if _rc == 0 {
            drop `role'
        }
    }
    forvalues k = 1/`n' {
        local role : word `k' of `roles'
        rename `t`k'' `role'
    }
end


* The label of the ordered pair: the values of source and target
* joined by an underscore, whether the nodes are named by strings or
* by numbers.
program define _netcalc_edgeid
    version 16.0
    capture confirm string variable source
    if _rc == 0 {
        qui gen edge_id = source + "_" + target
    }
    else {
        qui gen edge_id = strofreal(source, "%21.0g") + "_" ///
                        + strofreal(target, "%21.0g")
    }
end


* A figure that describes a node is repeated on every row that names
* the node, as source on the rows the node leaves and as target on
* the rows it enters. The rows must agree with one another at either
* end, and the two ends must agree with each other, since they carry
* the same figure of the same node. Data that break either rule are
* refused and the nodes are listed, with the figures that differ.
* Figures agree when they are equal to within floating-point error,
* a relative difference of 1e-12, so that a figure computed twice
* by the analyst, in two orders of summation, is not refused.
program define _netcalc_constant
    version 16.0
    syntax, Stem(string) [Feature(string)]
    local unit = cond("`feature'" != "", "node, period and subnet", ///
                                         "node and period")
    tempname W S T

    * the rows of a node agree with one another, at either end
    foreach end in source target {
        capture frame drop `W'
        frame put year `feature' `end' `end'_`stem', into(`W')
        frame `W' {
            qui collapse (min) lo = `end'_`stem' ///
                         (max) hi = `end'_`stem', ///
                by(year `feature' `end')
            qui keep if reldif(lo, hi) > 1e-12
            local n_bad = _N
            sort year `feature' `end'
        }
        if `n_bad' > 0 {
            di as error "`end'_`stem' is not the same on every row" ///
                        " of a `unit': it describes the node, so its" ///
                        " rows must agree"
            di as error "  the " `n_bad' " cases whose rows differ," ///
                        " with the smallest and the largest figure:"
            frame `W': _netcalc_show, vars(year `feature' `end' lo hi)
            di as error "Nothing has been written"
            capture frame drop `W'
            exit 459
        }
    }
    capture frame drop `W'

    * the figure of a node is the same whether the row names the node
    * as its source or as its target. The rows of a node agree to
    * within floating-point error by now, so one row of each stands
    * for them.
    frame put year `feature' source source_`stem', into(`S')
    frame `S' {
        qui collapse (first) as_source = source_`stem', ///
            by(year `feature' source)
        rename source node
    }
    frame put year `feature' target target_`stem', into(`T')
    frame `T' {
        qui collapse (first) as_target = target_`stem', ///
            by(year `feature' target)
        rename target node
        qui frlink 1:1 year `feature' node, frame(`S') ///
            generate(_netcalc_link)
        qui frget as_source, from(_netcalc_link)
        qui keep if reldif(as_source, as_target) > 1e-12
        local n_bad = _N
        sort year `feature' node
    }
    if `n_bad' > 0 {
        di as error "`stem' of a node differs between the rows that" ///
                    " name it as source and those that name it as" ///
                    " target"
        di as error "  the " `n_bad' " cases, by `unit', with the" ///
                    " figure at either end:"
        frame `T': _netcalc_show, vars(year `feature' node ///
                                      as_source as_target)
        di as error "Nothing has been written"
        capture frame drop `S'
        capture frame drop `T'
        exit 459
    }
    capture frame drop `S'
    capture frame drop `T'
end


* The rows the input must hold: every period, every level of the
* feature under subnet(multi), and every ordered pair of distinct
* nodes, the nodes being every name the data give as source or
* target. The rows are counted first, which is all a complete input
* costs: with no self-loop and no key twice, the data hold all of
* those rows exactly when they hold as many. Only when they fall
* short is the full set built, to list the rows they lack.
program define _netcalc_mesh
    version 16.0
    syntax [, Feature(string)]

    local cur = c(frame)
    qui count
    local n_rows = r(N)

    tempname YR NS NT FT
    tempfile years sources targets features

    frame put year, into(`YR')
    frame `YR' {
        qui duplicates drop
        local n_years = _N
        qui save `years'
    }

    * the nodes: every name that appears at either end of an edge
    frame put target, into(`NT')
    frame `NT' {
        rename target source
        qui save `targets'
    }
    frame put source, into(`NS')
    frame `NS' {
        qui append using `targets'
        qui duplicates drop
        local n_nodes = _N
        qui save `sources'
        rename source target
        qui save `targets', replace
    }

    local n_feat = 1
    if "`feature'" != "" {
        frame put `feature', into(`FT')
        frame `FT' {
            qui duplicates drop
            local n_feat = _N
            qui save `features'
        }
    }

    capture frame drop `YR'
    capture frame drop `NS'
    capture frame drop `NT'
    capture frame drop `FT'

    local n_need = `n_years' * `n_feat' * `n_nodes' * (`n_nodes' - 1)
    if `n_rows' == `n_need' {
        exit
    }

    * the full set of rows, and those the data lack
    tempname MS CT
    frame create `MS'
    frame `MS' {
        qui use `years'
        qui cross using `sources'
        qui cross using `targets'
        qui drop if source == target
        if "`feature'" != "" {
            qui cross using `features'
        }
        qui frlink 1:1 year `feature' source target, frame(`cur') ///
            generate(_netcalc_in)
        qui keep if missing(_netcalc_in)
        drop _netcalc_in
        local n_lack = _N
        sort year `feature' source target
    }

    di as error "the data are not the complete panel of their rows:" ///
                " `n_lack' of `n_need' rows are missing"
    frame copy `MS' `CT'
    frame `CT' {
        qui contract year, freq(rows_missing)
        di as error "  missing rows in each period:"
        list year rows_missing, noobs clean abbreviate(16)
    }
    capture frame drop `CT'
    di as error "  the missing rows:"
    frame `MS' {
        _netcalc_show, vars(year `feature' source target)
    }
    capture frame drop `MS'
    if "`feature'" != "" {
        di as error "Every period needs a row for each ordered pair of" ///
                    " the `n_nodes' nodes in each of the `n_feat'" ///
                    " levels of `feature';"
    }
    else {
        di as error "Every period needs a row for each ordered pair of" ///
                    " the `n_nodes' nodes;"
    }
    di as error "enter zero where nothing was recorded." ///
                " Nothing has been written"
    exit 459
end


* List the first rows that meet the condition, and say how many more
* there are, so that a refusal shows the rows it is about.
program define _netcalc_show
    version 16.0
    syntax [if] , Vars(string) [Max(integer 50)]
    marksample touse, novarlist
    qui count if `touse'
    local n = r(N)
    if `n' == 0 {
        exit
    }
    tempvar k
    qui gen long `k' = sum(`touse')
    list `vars' if `touse' & `k' <= `max', noobs clean abbreviate(16)
    if `n' > `max' {
        di as error "  ... and " `n' - `max' " more"
    }
end

*! _netcalc_frames v1.0.0
*! Dispatches the frame subcommands
*! Internal routine of network_calc; not for direct use

program define _netcalc_frames
    version 16.0
    
    * Parse subcommand
    gettoken subcmd 0 : 0 , parse(" ")
    
    if "`subcmd'" == "create_or_join" {
        _netcalc_join , `0'
    }
    else if "`subcmd'" == "aggregate" {
        _netcalc_aggregate , `0'
    }
    else {
        di as error "Unknown _netcalc_frames subcommand: `subcmd'"
        exit 198
    }
end


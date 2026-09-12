*! _netcalc_pool 2.0.0
*! Collapses multi-subnet raw data over the feature
*! Internal routine of network_calc; not for direct use

program define _netcalc_pool
    version 16.0
    syntax , Type(string) Feature(varname)

    * Turns a multi-subnet input panel into the single-subnet input
    * panel that describes the same edges without the feature split, so
    * that the single-subnet template can then be applied to it. This is
    * how a multi-subnet flow or attribute network reaches
    * networks_single: the raw data is combined first and the weight is
    * computed once, rather than the per-subnet weights being added up,
    * which would count each subnet as a whole network.
    *
    * interaction never arrives here. It has no single-subnet form, so
    * its subnet weights already carry the share of each subnet and are
    * simply summed.

    if !inlist("`type'", "flow", "attribute") {
        di as error "_netcalc_pool: type() must be flow or attribute"
        exit 198
    }

    qui {
        if "`type'" == "flow" {
            * The values are counts of what moved along the edge, so the
            * subnets combine by addition: every group travelling from
            * the source to the target becomes one flow.
            collapse (sum) source_value target_value, ///
                by(year source target)
        }
        else {
            * The values are levels describing a node, not quantities
            * that move, so the subnets combine by a weighted mean. The
            * weight is the share of the subnet in the node total, which
            * the feature split itself provides, so the node level is
            *     A_i = sum_X r_i^X * A_i^X,  r_i^X = A_i^X / sum_X A_i^X
            * A level is repeated on every edge of its node, so one row
            * per subnet is tagged before the sums are taken.
            tempvar sfirst tfirst ssum ssq tsum tsq asrc atgt

            bysort year `feature' source (target): ///
                gen byte `sfirst' = (_n == 1)
            bysort year source: ///
                gen double `ssum' = sum(source_value * `sfirst')
            by year source: ///
                gen double `ssq' = sum(source_value * source_value ///
                                       * `sfirst')
            by year source: gen double `asrc' = `ssq'[_N] / `ssum'[_N]

            bysort year `feature' target (source): ///
                gen byte `tfirst' = (_n == 1)
            bysort year target: ///
                gen double `tsum' = sum(target_value * `tfirst')
            by year target: ///
                gen double `tsq' = sum(target_value * target_value ///
                                       * `tfirst')
            by year target: gen double `atgt' = `tsq'[_N] / `tsum'[_N]

            collapse (firstnm) `asrc' `atgt', by(year source target)
            rename `asrc' source_value
            rename `atgt' target_value
        }
    }
end

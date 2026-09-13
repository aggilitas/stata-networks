netcalc: directed edge weights from node-level panel data
=========================================================

Necmi Talay
aggilitas@gmail.com


What the package does
---------------------

netcalc turns a long node-level panel into a panel of directed edge
weights, ready for a fixed-effects estimator such as reghdfe. One call
computes one network and adds it as a variable to a Stata frame, so
several calls build a multi-network edge panel side by side.

Three templates are available.

  interaction   the share of the target node in what a subnet holds
                outside the source. Requires the panel to be split into
                subnets by a feature; it has no single-subnet form.

  flow          the share of an edge in the total leaving its node in
                that period. For quantities that move between nodes:
                migration, trade, capital.

  attribute     the log ratio of the two node values. For levels that
                describe nodes rather than move between them: GDP,
                unemployment, schooling.

flow and attribute accept a feature as well. A subnet is a network of
its own, whose weights add up to one, and size gives it the share it
takes when the subnets are put back together, so the single-subnet copy
is the weight of the edge in the node as a whole. An attribute weight is
a log ratio, which does not add up that way, so an attribute network
with subnets stays in the multi-subnet frame.

Input is a long panel. Without a feature it holds year, source, target,
source_value and target_value. With a feature it holds the feature and
two columns more on each side, source_size and target_size, which carry
what the subnet weighs at that node.

Results are written to the frames networks_single and networks_multi,
keyed on year and edge_id, and on year, feature and edge_id. A
multi-subnet call writes a second column beside the weights, named
after the network with _fratio added, holding the share the subnet
takes at its node.


Requirements
------------

Stata 16 or later, because the package writes into frames.


Files
-----

  network_calc.ado           the command; the only public name
  network_calc.sthlp         help file
  _netcalc_interaction.ado   interaction template
  _netcalc_flow.ado          flow template
  _netcalc_attribute.ado     attribute template
  _netcalc_join.ado          creates an output frame or joins to it
  _netcalc_aggregate.ado     sums subnet weights over the feature

Names beginning with an underscore are internal routines and are not
meant to be called directly.

  network_calc_cert.do       certification script


Installation
------------

From the Stata Journal archive:

    net install netcalc, from(http://www.stata-journal.com/software/sjXX-X)

From the development repository:

    net install netcalc, from(https://raw.githubusercontent.com/aggilitas/stata-networks/main/)

If a version before 2.0.0 is installed, it was distributed under the
package name stata-networks. Remove it first, or both copies will sit
in the ado directory and shadow each other. ado uninstall takes the
number ado dir prints in brackets beside the package, not its name:

    ado dir
    ado uninstall [n]


Certification
-------------

network_calc_cert.do builds its own data and asserts the properties that
define the weights: that the weights leaving a node sum to one, that
attribute weights cancel along a reversed edge, and that scaling the
whole input by a positive constant moves no weight. It stops at the
first failure.


Citation
--------

Citation is a condition of the licence. Any work that uses this command,
or results derived from it, must cite:

    Talay, N., H. Acaroglu, A. Gunal, and F. P. Garcia Marquez. 2026.
    Algebraic invariant multilayer network edge regression: Multi-source
    data fusion with macro-shock immunity. Knowledge-Based Systems
    117007. https://doi.org/10.1016/j.knosys.2026.117007

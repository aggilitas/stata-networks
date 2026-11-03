netcalc: directed edge variables from a panel of ordered node pairs
===================================================================

Necmi Talay
aggilitas@gmail.com

Version 2.2.0. The package is called netcalc, its one command is
network_calc, and stata-networks is the name of the repository in
which it is developed.


What the package does
---------------------

netcalc turns a long panel, one observation per ordered pair of nodes
and period, and per subnet when the panel is split by a feature, into a
panel of directed edge variables, ready for a fixed-effects estimator
such as reghdfe. One call computes one network and adds it as a
variable to a Stata frame, so several calls build a multi-network edge
panel side by side.

Three templates are available.

  interaction   the quantity of a subnet at the target over its quantity
                at every node but the source, with the subnets added up
                in proportion to their size at the source. Requires the
                panel to be split into subnets by a feature; a feature
                with one level gives a network with one subnet.

  flow          the quantity of an edge over the total leaving its node
                in that period. For quantities that move between nodes:
                migration, trade, capital.

  attribute     the log ratio of the two node values. For levels that
                describe nodes rather than move between them: GDP,
                unemployment, schooling.

flow accepts a feature as well. A subnet is a network of its own, whose
weights add up to one, and size gives it the ratio it takes when the
subnets are put back together, so the single-subnet copy is the weight
of the edge in the node as a whole. An attribute describes the node and
has no subnets: the node level is passed with subnet(single).

Input is the complete panel of its rows: every period, every ordered
pair of distinct nodes and, with a feature, every level of the feature,
with one value for each node under interaction and attribute, one for
each edge under flow, and a zero, which the data supply, for a flow or
an interaction that did not happen. A row missing from that panel is
refused, and the command lists it. Without a feature it holds year,
source, target, source_value and target_value, or the variables named
in period(), source(), target() and value(). Under flow both value
columns describe the edge: source_value as the source records it and
target_value as the target records it; direction(outflow) reads the
first and direction(inflow) the second. With a feature the panel holds
the feature and two columns more on each side, source_size and
target_size, or the variables named in size(), which carry what the
subnet weighs at that node and are read as a ratio of the subnet to the
node. A figure that describes a node, under interaction the size and
the value of a subnet at its node and under attribute the level of the
node, is repeated on every row that names the node, and data in which
those rows disagree are refused, with the cases listed. Nodes may be
named by strings or by numbers.

Results are written to the frames networks_single and networks_multi,
keyed on year, source and target, and on year, feature, source and
target; edge_id, the two node names joined by an underscore, is carried
beside them as a label of the pair. A multi-subnet call writes a second
column beside the weights, named after the network with _fratio added,
holding the ratio of the subnet within the feature at its node. A
network joins a frame only with the rows the frame holds: a call whose
rows differ is refused, and the rows on either side are listed. Nothing
is filled in. Every join is checked against both frames before either
is written. A name a frame already holds is refused unless replace is
specified, which clears it from both frames once every check has
passed. A total of zero is not refused: the weights read over it are
written as zero, the command says how many totals came to zero, and
returns the count in r().


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
  network_calc_cert.log      its log, run on Stata 17

  generate_test_data.do      builds the data files the session reads,
                             with its log: 81 nodes over six years,
                             the people of each node grouped by the
                             node they were born in. The files are not
                             distributed; the two multi-subnet ones
                             hold 3,149,280 rows each, so they are
                             built where they are used
  generate_test_data.log     its log
  example_session.do         the session shown in the article, ending
                             in an estimation with three standard
                             errors; needs reghdfe and ftools
  example_session.log        its log
  example_estimates.csv      the estimates the session writes
  article_table2.csv         the first row of each file the session
                             reads, table 2 of the article

The files generate_test_data.do builds, in the directory it is run
from: test_interaction_multi.csv, test_flow_multi.csv,
test_flow_single.csv and test_attribute_single.csv, the four files the
session reads, and test_outcome.csv, the outcome it estimates.


Installation
------------

From the Stata Journal archive, under the name the Journal gives the
package once the article is accepted, which takes the place of st0XXX:

    net install st0XXX, from(http://www.stata-journal.com/software/sjXX-X)

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

network_calc_cert.do builds its own data, six nodes over three periods
and three subnets on a complete directed grid, and asserts properties
the weights must have, and values worked out by hand for one edge,
rather than numbers recorded from an earlier run. It stops at the first
failure. Its eight sections check:

  1. that a subnet's weights sum to one, that the ratios of a node sum
     to one, and that the single-subnet copy sums to one
  2. that attribute values cancel along a reversed edge, and that an
     attribute with subnets is refused
  3. that scaling the whole input by a positive constant, by a factor
     that changes from one period to the next, or everything one source
     sends by a factor of its own, moves no weight
  4. that direction(inflow) anchors the weight at the target, the
     value recorded there over the total recorded there
  5. that a second network joins a frame only with the rows the frame
     holds, that a network with a node, a period or a subnet more or
     fewer, or split by another feature, is refused and writes
     nothing, and that a call refused at the second frame writes
     neither
  6. that the command refuses each input it cannot make a network of,
     self-loops, a row missing from the complete panel and a node
     figure that differs between its rows included, that nodes may be
     numbers or hold underscores, that option values ignore case, that
     a name is checked exactly, that a frame holding _merge is refused,
     and that replace clears a name from both frames once every check
     has passed
  7. that the weights of one edge equal the numbers worked out by hand
     from the formulas that build the data
  8. that r() reports the call and counts the totals that are zero,
     that the variables may be named by options, and that the data in
     memory come back as they were found, with their file name and
     changed flag


Notes
-----

Section 6.7 of the article sets out the published application of the
framework, job-seeking migration between the 81 provinces of Turkiye
(Talay et al. 2026, cited below), as the network_calc calls that build
its columns. Its migration and birthplace counts are not public: the
Turkish Statistical Institute supplies them for a fee, and they cannot
be distributed; the unemployment and schooling levels are published,
but without the counts the calls cannot be run. The package therefore
holds neither the data of that application nor a log of its calls.
The example session runs on
synthetic data instead, of the same shape, built by
generate_test_data.do, which serve for testing.


Citation
--------

If you use network_calc, please cite the article that sets out the
framework it implements:

    Talay, N., H. Acaroglu, A. Gunal, and F. P. Garcia Marquez. 2026.
    Algebraic invariant multilayer-network edge regression: Multi-source
    data fusion with macro-shock immunity. Knowledge-Based Systems 352:
    117007. https://doi.org/10.1016/j.knosys.2026.117007

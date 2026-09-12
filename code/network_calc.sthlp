{smcl}
{* *! version 2.0.0  12sep2026}{...}
{viewerjumpto "Syntax" "network_calc##syntax"}{...}
{viewerjumpto "Description" "network_calc##description"}{...}
{viewerjumpto "Options" "network_calc##options"}{...}
{viewerjumpto "Input data" "network_calc##input"}{...}
{viewerjumpto "Templates" "network_calc##templates"}{...}
{viewerjumpto "Output frames" "network_calc##output"}{...}
{viewerjumpto "Examples" "network_calc##examples"}{...}
{viewerjumpto "Stored results" "network_calc##results"}{...}
{viewerjumpto "Author" "network_calc##author"}{...}

{title:Title}

{phang}
{bf:network_calc} {hline 2} Directed edge weights from node-level panel
data


{marker syntax}{...}
{title:Syntax}

{p 8 16 2}
{cmd:network_calc}{cmd:,}
{opt t:ype(template)}
{opt s:ubnet(scope)}
{opt n:ame(netname)}
[{it:options}]

{synoptset 26 tabbed}{...}
{synopthdr}
{synoptline}
{syntab:Required}
{synopt :{opt t:ype(template)}}edge weight template:
{cmd:interaction}, {cmd:flow} or {cmd:attribute}{p_end}
{synopt :{opt s:ubnet(scope)}}{cmd:single} for one network,
{cmd:multi} for one network per feature{p_end}
{synopt :{opt n:ame(netname)}}name of the network; must be a valid
variable name{p_end}

{syntab:Optional}
{synopt :{opt f:eature(varname)}}variable that splits the network into
subnets; required with {cmd:subnet(multi)}{p_end}
{synopt :{opt d:irection(direction)}}{cmd:outflow} (default) or
{cmd:inflow}{p_end}
{synopt :{opt debug}}display intermediate output{p_end}
{synoptline}

{pstd}
{cmd:network_calc} requires Stata 16 or later, because it writes its
results into {help frames}.


{marker description}{...}
{title:Description}

{pstd}
{cmd:network_calc} turns a long node-level panel into a panel of
directed edge weights, ready for a fixed-effects estimator such as
{help reghdfe} or {cmd:ivreghdfe}. One call computes one network and
adds it as a variable to a frame, so several calls build a
multi-network edge panel side by side.

{pstd}
The data in memory is not the output: the calculated weights are
written to the frames described under
{help network_calc##output:Output frames}, and the data in memory is
restored when the command finishes. Observations with a missing value
in any required variable are dropped before the calculation, and those
are not restored.


{marker options}{...}
{title:Options}

{phang}
{opt t:ype(template)} selects the weight template and is required. See
{help network_calc##templates:Templates} for the three formulas.

{phang}
{opt s:ubnet(scope)} is required. {cmd:single} computes one weight per
edge and period. {cmd:multi} computes one weight per edge, period and
level of {cmd:feature()}, and additionally builds a single-subnet copy;
see {help network_calc##output:Output frames} for how that copy is
formed, which differs by template.

{phang}
{opt n:ame(netname)} is required and names the network. The name
becomes the variable that holds the weights in the output frames, so it
must be a valid Stata variable name and must not already be taken by
another network in the same frame.

{phang}
{opt f:eature(varname)} names the variable that splits the network into
subnets: birthplace, ethnicity, sector, commodity class, and so on. It
is required with {cmd:subnet(multi)}. With {cmd:subnet(single)} it is
ignored, and a note says so.

{phang}
{opt d:irection(direction)} chooses which node anchors the weight. With
{cmd:outflow}, the default, the weights of the edges leaving a node are
computed relative to that node. With {cmd:inflow} the two node roles
are exchanged, so the weights of the edges entering a node are computed
relative to it. For {cmd:interaction} and {cmd:flow} the choice decides
which of the two sums equals one; for {cmd:attribute} it flips the sign
of the log ratio.

{phang}
{opt debug} displays the intermediate quantities of the template and a
summary of the calculated weights. Use it to see why a weight is
missing or unexpected.


{marker input}{...}
{title:Input data}

{pstd}
The data in memory must be in long form, one observation per directed
edge and period, and must contain these variables under these names:

{p2colset 9 30 32 2}{...}
{p2col :{cmd:year}}period identifier{p_end}
{p2col :{cmd:source}}node the edge leaves{p_end}
{p2col :{cmd:target}}node the edge enters{p_end}
{p2col :{cmd:source_value}}value attached to {cmd:source}{p_end}
{p2col :{cmd:target_value}}value attached to {cmd:target}{p_end}
{p2colreset}{...}

{pstd}
With {cmd:subnet(multi)} the variable named in {cmd:feature()} must be
present as well, and the panel must hold one observation per period,
feature and directed edge.

{pstd}
{cmd:source} and {cmd:target} must be string variables, because the
edge identifier is built by joining them. Choose node names that
contain no underscore, so that the identifier stays unambiguous.

{pstd}
{cmd:source_value} is expected to be constant within a period, feature
and source, because it describes the source node rather than the edge;
{cmd:target_value} varies over targets in the same way.


{marker templates}{...}
{title:Templates}

{dlgtab:interaction}

{pstd}
{cmd:type(interaction)} requires {cmd:subnet(multi)}. The weight is the
share of the feature at the source node, multiplied by the share of the
same feature at the target node among all other nodes:

{p 8 8 2}
e(ij,X) = [N(i,X) / N(i)] * [n(j,X) / sum over k != i of N(k,X)]

{pstd}
The weights leaving a node sum to one in every period, so over a
complete grid of n nodes the mean weight is 1/(n-1).

{dlgtab:flow}

{pstd}
{cmd:type(flow)} accepts either scope. The weight is the share of the
edge in the total leaving its node in that period, and under
{cmd:subnet(multi)} in the total within that feature as well:

{p 8 8 2}
w(ij) = v(ij) / T(year, source)

{pstd}
Use it for quantities that move between nodes: migration, trade,
capital.

{dlgtab:attribute}

{pstd}
{cmd:type(attribute)} accepts either scope. The weight is the log ratio
of the two node values:

{p 8 8 2}
w(ij) = ln[A(j) / A(i)]     under {cmd:direction(outflow)}

{pstd}
Use it for levels that describe nodes rather than move between them:
GDP, unemployment, schooling. The log ratio is undefined when either
value is zero or negative; such an edge is kept with a missing weight,
and {cmd:r(n_valid)} reports how many weights are defined.


{marker output}{...}
{title:Output frames}

{pstd}
{cmd:network_calc} writes into two frames, creating a frame on the
first call and merging into it on later calls:

{p2colset 9 28 30 2}{...}
{p2col :{cmd:networks_single}}keyed on {cmd:year} and
{cmd:edge_id}{p_end}
{p2col :{cmd:networks_multi}}keyed on {cmd:year}, {cmd:feature} and
{cmd:edge_id}{p_end}
{p2colreset}{...}

{pstd}
{cmd:edge_id} is {cmd:source} and {cmd:target} joined by an underscore.
Every call adds one variable, named by {cmd:name()}, to
{cmd:networks_single}; a {cmd:subnet(multi)} call adds it to both
frames.

{pstd}
How the single-subnet copy of a {cmd:subnet(multi)} network is built
depends on the template, because a subnet weight is a share within its
own subnet and adding such shares would count every subnet as a whole
network:

{phang2}
{cmd:flow} and {cmd:attribute} have a single-subnet form of their own,
so the raw data is combined over the feature first and the weight is
then computed once from it. Counts are added, because every group
moving from the source to the target is part of one flow. Levels are
averaged over the subnets, weighted by the share of each subnet in the
node total, because a level describes a node rather than moving between
nodes.

{phang2}
{cmd:interaction} has no single-subnet form: its weight already carries
the share of each subnet, so the subnet weights are added.

{pstd}
The weight a subnet carries in that average is its share of the node
total, A(i,X) / sum over X of A(i,X), so the weights of a node sum to
one.

{pstd}
Later calls merge one to one on the keys above, so a network whose
edges do not match those already in the frame contributes missing
values. The command reports how many.


{marker examples}{...}
{title:Examples}

{pstd}One network from migration flows{p_end}
{phang2}{cmd:. use migration.dta, clear}{p_end}
{phang2}{cmd:. network_calc, type(flow) subnet(single) name(migration)}{p_end}

{pstd}The same flows seen from the receiving node{p_end}
{phang2}{cmd:. network_calc, type(flow) subnet(single) name(mig_in)}{break}
{cmd:          direction(inflow)}{p_end}

{pstd}Social connection by birthplace, one subnet per birthplace{p_end}
{phang2}{cmd:. use birthplace.dta, clear}{p_end}
{phang2}{cmd:. network_calc, type(interaction) subnet(multi)}{break}
{cmd:          feature(birthplace) name(birth_place)}{p_end}

{pstd}Income disparity between the two nodes of each edge{p_end}
{phang2}{cmd:. use gdp.dta, clear}{p_end}
{phang2}{cmd:. network_calc, type(attribute) subnet(single) name(gdp)}{p_end}
{phang2}{cmd:. display r(n_valid) " of " r(n_edges) " weights defined"}{p_end}

{pstd}Estimating on the edge panel the calls have built{p_end}
{phang2}{cmd:. frame change networks_single}{p_end}
{phang2}{cmd:. reghdfe migration birth_place gdp, absorb(edge_id)}{p_end}

{pstd}The multi-subnet panel, with the feature as a second
dimension{p_end}
{phang2}{cmd:. frame change networks_multi}{p_end}
{phang2}{cmd:. reghdfe migration birth_place, absorb(edge_id feature)}{p_end}


{marker results}{...}
{title:Stored results}

{pstd}
{cmd:network_calc} stores the following in {cmd:r()}:

{synoptset 24 tabbed}{...}
{p2col 5 24 28 2: Scalars}{p_end}
{synopt:{cmd:r(n_edges)}}number of edge weights calculated{p_end}
{synopt:{cmd:r(mean_weight)}}mean of the calculated weights{p_end}
{synopt:{cmd:r(n_valid)}}number of weights that are not missing;
{cmd:type(attribute)} only{p_end}

{p2col 5 24 28 2: Macros}{p_end}
{synopt:{cmd:r(network_name)}}name given in {cmd:name()}{p_end}
{synopt:{cmd:r(network_type)}}template given in {cmd:type()}{p_end}
{synopt:{cmd:r(subnet_type)}}scope given in {cmd:subnet()}{p_end}
{p2colreset}{...}


{marker author}{...}
{title:Author}

{pstd}
Necmi Talay{break}
{browse "mailto:aggilitas@gmail.com":aggilitas@gmail.com}{break}
{browse "https://github.com/aggilitas/stata-networks":stata-networks}


{marker citation}{...}
{title:Citation}

{pstd}
Citation is a condition of the licence. Any work that uses this
command, or results derived from it, must cite:

{phang}
Talay, N., H. Acaroglu, A. Gunal, and F. P. Garcia Marquez. 2026.
Algebraic invariant multilayer network edge regression: Multi-source
data fusion with macro-shock immunity. {it:Knowledge-Based Systems}
117007. {browse "https://doi.org/10.1016/j.knosys.2026.117007"}


{marker alsosee}{...}
{title:Also see}

{psee}
Online: {help frames}, {help reghdfe} (if installed)
{p_end}

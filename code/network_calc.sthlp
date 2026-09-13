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
restored when the command finishes, unchanged.

{pstd}
The command refuses data it cannot make a network of, rather than
returning a weight that reads as defined. It stops on a missing value
in any required variable; on a negative size or a negative flow; on an
{cmd:attribute} value that is zero or negative, the log ratio being
undefined there; and on a zero denominator, which is a node holding
none of any subnet, a node whose edges are all zero, or a subnet
absent from every node but its source. A subnet the node does not hold
at all is the one zero that is allowed: its share is zero, so its
edges weigh nothing whatever the flows say.

{pstd}
Dropping the offending edge instead would take it out of its own
denominator, and the weights that remained would still add up to one,
over a mesh quietly missing one of its alternatives.


{marker options}{...}
{title:Options}

{phang}
{opt t:ype(template)} selects the weight template and is required. See
{help network_calc##templates:Templates} for the three formulas.

{phang}
{opt s:ubnet(scope)} is required. {cmd:single} computes one weight per
edge and period from single-subnet data. {cmd:multi} computes one
weight per edge, period and level of {cmd:feature()}, and for
{cmd:interaction} and {cmd:flow} also a single-subnet copy; see
{help network_calc##output:Output frames}.

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
computed relative to that node. {cmd:inflow} exchanges the two indices
and nothing else: the weight written on edge i,j is the weight the same
formula gives to edge j,i. For {cmd:interaction} and {cmd:flow} that
decides which of the two sums equals one, so the weights of a node add
up over the edges entering it rather than those leaving it; for
{cmd:attribute} it flips the sign of the log ratio. Nothing in the data
moves either way and the edge keeps its own orientation: only which
columns are read as the source changes.

{phang}
{opt debug} displays the intermediate quantities of the template and a
summary of the calculated weights. Use it to see why a weight is not
what you expected.


{marker input}{...}
{title:Input data}

{pstd}
The data in memory must be in long form, one observation per directed
edge and period. Without a feature it must hold:

{p2colset 9 30 32 2}{...}
{p2col :{cmd:year}}period identifier{p_end}
{p2col :{cmd:source}}node the edge leaves{p_end}
{p2col :{cmd:target}}node the edge enters{p_end}
{p2col :{cmd:source_value}}quantity measured at {cmd:source}{p_end}
{p2col :{cmd:target_value}}quantity measured at {cmd:target}{p_end}
{p2colreset}{...}

{pstd}
With {cmd:subnet(multi)} the panel holds one observation per period,
subnet and directed edge, and carries two columns more:

{p2colset 9 30 32 2}{...}
{p2col :{cmd:year}}period identifier{p_end}
{p2col :{it:feature}}the variable named in {cmd:feature()}, which
splits each node into subnets{p_end}
{p2col :{cmd:source}}node the edge leaves{p_end}
{p2col :{cmd:target}}node the edge enters{p_end}
{p2col :{cmd:source_size}}weight of the subnet at {cmd:source}{p_end}
{p2col :{cmd:source_value}}quantity measured at {cmd:source}{p_end}
{p2col :{cmd:target_size}}weight of the subnet at {cmd:target}{p_end}
{p2col :{cmd:target_value}}quantity measured at {cmd:target}{p_end}
{p2colreset}{...}

{pstd}
{cmd:size} is what the subnet weighs at that node: the people born in
a given province who live there, the passengers carried by a given mode,
whatever the subnets are counted in. {cmd:value} is the quantity the
network is about. What belongs in {cmd:value} follows from the feature:
splitting an edge by transport mode makes a distance in kilometres
meaningless and a fare or a tonnage meaningful.

{pstd}
{cmd:size} is constant within a period, subnet and node, because it
describes the node rather than the edge. {cmd:value} is constant in the
same way when it describes a node, as in {cmd:attribute}, and varies
over the edge when it travels along it, as in {cmd:flow}.

{pstd}
{cmd:source} and {cmd:target} must be string variables, because the
edge identifier is built by joining them. Choose node names that
contain no underscore, so that the identifier stays unambiguous.


{marker templates}{...}
{title:Templates}

{dlgtab:interaction}

{pstd}
{cmd:type(interaction)} requires {cmd:subnet(multi)}: it compares two
subnets of two nodes and has no single-subnet form. The weight is the
share of the subnet at the source node, multiplied by the share of the
target node in what the subnet holds outside the source. The first
share is read from {cmd:size}, the second from {cmd:value}:

{p 8 8 2}
e(ij,X) = [S(i,X) / S(i)] * [v(j,X) / sum over k != i of v(k,X)]

{pstd}
How much of the source node is this subnet, times how much of the
quantity the subnet carries, outside the source node, sits at the
target. Where the subnet is itself what is being measured, as with
people grouped by birthplace, {cmd:size} and {cmd:value} hold the same
number.

{dlgtab:flow}

{pstd}
{cmd:type(flow)} accepts either scope. Under {cmd:subnet(single)} the
weight is the share of the edge in what leaves its node in that period:

{p 8 8 2}
w(ij) = v(ij) / sum over j of v(ij)

{pstd}
Under {cmd:subnet(multi)} that share is taken within the subnet and
scaled by the share of the subnet itself, so that the weights of a node
add up to one over subnets and targets together:

{p 8 8 2}
w(ij,X) = [S(i,X) / S(i)] * [v(ij,X) / sum over j of v(ij,X)]

{pstd}
Use it for quantities that travel along the edge: migration, trade,
capital.

{dlgtab:attribute}

{pstd}
{cmd:type(attribute)} accepts either scope. The weight is the log ratio
of the two node values:

{p 8 8 2}
w(ij) = ln[A(j) / A(i)]     under {cmd:direction(outflow)}

{pstd}
Under {cmd:subnet(multi)} the ratio is taken between the same subnet at
the two nodes. {cmd:size} is not used, because a log ratio compares two
specific subnets and nothing is being weighted.

{pstd}
Use it for levels that describe nodes rather than travel between them:
GDP, unemployment, schooling. The log ratio is undefined when either
value is zero or negative, so both values must be positive; an input
that is not is refused.


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
Every call adds one variable, named by {cmd:name()}, to the frame or
frames it writes:

{p2colset 9 34 36 2}{...}
{p2col :{cmd:subnet(single)}}{cmd:networks_single}{p_end}
{p2col :{cmd:interaction}, {cmd:subnet(multi)}}both{p_end}
{p2col :{cmd:flow}, {cmd:subnet(multi)}}both{p_end}
{p2col :{cmd:attribute}, {cmd:subnet(multi)}}{cmd:networks_multi}
only{p_end}
{p2colreset}{...}

{pstd}
A frame is a panel of edges, and every network in it is a column of
that panel, so the networks must be computed over the same edges. The
merge keeps the union of the two edge sets, so no row is ever lost,
and the call reports how many edges matched and how many were on one
side only.

{pstd}
An edge a network does not reach is not a gap in that network: the
weight there is zero, and those cells are filled with zero so that no
row is lost to an estimator. Nothing already in the frame moves. For
{cmd:interaction} and {cmd:flow} the total the weights were divided by
never counted that edge; an {cmd:attribute} weight is a log ratio and
is part of no total at all, and an edge the network does not reach
holds no value at either end, so the two carry no difference and the
log of their ratio is zero. Only the cells the merge itself introduced
are filled.

{pstd}
A network that shares no edge at all with the frame is reported as
such, and the frame then holds the two of them stacked rather than
side by side. That is what happens when two multi-subnet networks are
split by different features, whose labels cannot meet, or when the
node names differ between the input files.

{pstd}
The copy in {cmd:networks_single} is the sum of the subnet weights.
That is what a subnet weight is built for in {cmd:interaction} and
{cmd:flow}: it carries the share of its own subnet, the shares of a
node add up over the subnets, and the sum is therefore the weight of
the edge in the node as a whole.

{pstd}
An {cmd:attribute} weight is a log ratio, which does not work that way:
adding log ratios over subnets multiplies the ratios, and the result
grows with the number of subnets rather than describing the node. So an
attribute network with subnets stays in {cmd:networks_multi}, and the
command says so when it runs. For a single-subnet attribute network,
reduce the node levels yourself and pass them with
{cmd:subnet(single)}.

{pstd}
A network read at the two resolutions is not the same calculation. A
single-subnet network computed from single-subnet data and the
single-subnet copy of a {cmd:subnet(multi)} call answer different
questions and will not agree in general.


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

{pstd}Migration split by the birthplace of the migrants{p_end}
{phang2}{cmd:. use migration_by_birthplace.dta, clear}{p_end}
{phang2}{cmd:. network_calc, type(flow) subnet(multi)}{break}
{cmd:          feature(birthplace) name(mig_bp)}{p_end}

{pstd}Income disparity between the two nodes of each edge{p_end}
{phang2}{cmd:. use gdp.dta, clear}{p_end}
{phang2}{cmd:. network_calc, type(attribute) subnet(single) name(gdp)}{p_end}

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

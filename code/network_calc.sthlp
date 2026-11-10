{smcl}
{* *! version 2.2.0  10nov2026}{...}
{viewerjumpto "Syntax" "network_calc##syntax"}{...}
{viewerjumpto "Description" "network_calc##description"}{...}
{viewerjumpto "Options" "network_calc##options"}{...}
{viewerjumpto "Input data" "network_calc##input"}{...}
{viewerjumpto "Templates" "network_calc##templates"}{...}
{viewerjumpto "Output frames" "network_calc##output"}{...}
{viewerjumpto "Examples" "network_calc##examples"}{...}
{viewerjumpto "Stored results" "network_calc##results"}{...}
{viewerjumpto "Characteristics" "network_calc##chars"}{...}
{viewerjumpto "Author" "network_calc##author"}{...}

{title:Title}

{phang}
{bf:network_calc} {hline 2} Directed edge variables from a panel of ordered
node pairs and periods


{marker syntax}{...}
{title:Syntax}

{p 8 16 2}
{cmd:network_calc}{cmd:,}
{opt t:ype(template)}
{opt s:ubnet(scope)}
{opt n:ame(newvar)}
[{it:options}]

{synoptset 26 tabbed}{...}
{synopthdr}
{synoptline}
{syntab:Required}
{synopt :{opt t:ype(template)}}construction template:
{cmd:interaction}, {cmd:flow} or {cmd:attribute}{p_end}
{synopt :{opt s:ubnet(scope)}}{cmd:single} for one network,
{cmd:multi} for one network per feature{p_end}
{synopt :{opt n:ame(newvar)}}name of the network; must be a valid
variable name{p_end}

{syntab:Optional}
{synopt :{opt f:eature(varname)}}variable that splits the network into
subnets; required with {cmd:subnet(multi)}{p_end}
{synopt :{opt d:irection(direction)}}{cmd:outflow} (default) or
{cmd:inflow}{p_end}
{synopt :{opt per:iod(varname)}}period variable; default
{cmd:year}{p_end}
{synopt :{opt so:urce(varname)}}node the edge leaves; default
{cmd:source}{p_end}
{synopt :{opt ta:rget(varname)}}node the edge enters; default
{cmd:target}{p_end}
{synopt :{opt v:alue(varlist)}}the two value variables, at the source and
at the target; default {cmd:source_value target_value}{p_end}
{synopt :{opt si:ze(varlist)}}the two size variables, with
{cmd:subnet(multi)}; default {cmd:source_size target_size}{p_end}
{synopt :{opt replace}}write over a network of the same name in the
output frames{p_end}
{synopt :{opt debug}}display intermediate output{p_end}
{synoptline}

{pstd}
{cmd:network_calc} requires Stata 16 or later, because it writes its
results into {help frames}.


{marker description}{...}
{title:Description}

{pstd}
{cmd:network_calc} turns a long panel, one observation per ordered pair
of nodes and period, and per subnet when the panel is split by a
feature, into a panel of directed edge variables, ready for a
fixed-effects estimator such as {help reghdfe} or {cmd:ivreghdfe}. One
call computes one network and adds it as a variable to a frame, so
several calls build a multi-network edge panel side by side.

{pstd}
The data in memory is not the output: the calculated networks are
written to the frames described under
{help network_calc##output:Output frames}, and the data in memory is
restored when the command finishes, unchanged.

{pstd}
The command refuses data it cannot make a network of, rather than
returning a value that reads as defined, and lists the rows a refusal
is about. It stops on a missing value in any required variable; on a
row missing from the complete panel described under
{help network_calc##input:Input data}; on a negative size, a negative
flow or a negative {cmd:interaction} value; on an {cmd:attribute} value
that is zero or negative, the log ratio being undefined there; on a row
whose {cmd:source} and {cmd:target} are the same node, which is not one
of its own alternatives; on an edge that appears more than once in a
period, or in a subnet; on a figure that describes a node and differs
between the rows that repeat it, under {cmd:interaction} the size and
the value of a subnet at its node and under {cmd:attribute} the level
of the node; and on a {cmd:source} and a {cmd:target} of different
kinds, one a string and the other numeric. It also stops, before either
output frame is written, on a join the frames cannot take: a network
whose rows are not those of the frame it joins, a multi-subnet network
split by a feature of another name, a key of another storage type than
the frame has, and a frame that holds a variable named {cmd:_merge} (see
{help network_calc##output:Output frames}). A zero denominator is not
refused. A node out of which nothing travels and a subnet whose value
is zero at every node but the source come to zero, and their weights
are written as zero; a subnet whose size at the node is zero keeps its
weights and has a ratio of zero there. The command says how many
totals came to zero and returns the counts in {cmd:r()}.

{pstd}
Dropping the offending edge instead would take it out of its own
denominator, and the weights that remained would still add up to one,
over a mesh quietly missing one of its alternatives.


{marker options}{...}
{title:Options}

{phang}
{opt t:ype(template)} selects the template and is required. See
{help network_calc##templates:Templates} for the three formulas. The
values of {cmd:type()}, {cmd:subnet()} and {cmd:direction()} may be
typed in any case and shortened to any unambiguous leading part, as in
{cmd:type(Flow)}, {cmd:type(f)} or {cmd:direction(IN)}.

{phang}
{opt s:ubnet(scope)} is required. {cmd:single} computes one value per
edge and period from single-subnet data. {cmd:multi} computes one
weight per edge, period and level of {cmd:feature()}, and a
single-subnet copy; see {help network_calc##output:Output frames}.
{cmd:multi} is for {cmd:interaction} and {cmd:flow}. An
{cmd:attribute} describes the node and has no subnets, so
{cmd:type(attribute)} takes {cmd:subnet(single)} only.

{phang}
{opt n:ame(newvar)} is required and names the network. The name
becomes the variable that holds the network in the output frames, so it
must be a valid Stata variable name and, unless {cmd:replace} is
specified, must not already be taken in either output frame:
{cmd:networks_single} and {cmd:networks_multi} are both checked,
whichever of them the call writes. The same holds for
{it:newvar}{cmd:_fratio}, the column a {cmd:subnet(multi)} call writes
beside the network, and under {cmd:subnet(multi)} the name has at most
25 characters, so that {it:newvar}{cmd:_fratio} fits in 32. The name
cannot be {cmd:netcalc_fratio} or {cmd:_merge}, which the command uses
on its own. The check is exact: a name that only abbreviates a variable
in a frame is a new name. Nor can it be
{cmd:year}, {cmd:source}, {cmd:target}, {cmd:edge_id} or {cmd:feature},
the variables of the frames themselves.

{phang}
{opt f:eature(varname)} names the variable that splits the network into
subnets: birthplace, ethnicity, sector, commodity class, and so on. It
is required with {cmd:subnet(multi)}. With {cmd:subnet(single)} it is
ignored, and a note says so.

{phang}
{opt d:irection(direction)} chooses which node anchors the weight. With
{cmd:outflow}, the default, the weights of the edges leaving a node are
computed relative to that node. With {cmd:inflow} the weight is anchored
at the target. Under {cmd:flow}, the weight of edge i,j is then the
value of that edge as recorded at j, read from {cmd:target_value}, over
the values recorded at j for every edge entering it: the weight of i in
what arrives at j. It is not the outflow weight of the reversed edge.
Under {cmd:interaction} the data describe the subnets at the nodes,
not the edges, so the exchange writes on the edge from i to j the
outflow weight of the edge from j to i; for {cmd:attribute} the log
ratio changes sign. For
{cmd:interaction} and {cmd:flow} the weights of a node then add up over
the edges entering it rather than those leaving it. Nothing in the data
moves either way and the edge keeps its own orientation.

{phang}
{opt per:iod(varname)}, {opt so:urce(varname)}, {opt ta:rget(varname)},
{opt v:alue(varlist)} and {opt si:ze(varlist)} name the variables the
command reads, where the data do not carry them under the default names
listed under {help network_calc##input:Input data}. {cmd:value()} and
{cmd:size()} take two variables each, the one at the source first and
the one at the target second; {cmd:size()} is read with
{cmd:subnet(multi)} only, and ignored otherwise, with a note. One
variable fills one role, and the feature cannot fill any, nor bear one
of the default names or the name {cmd:edge_id}, {cmd:edge_value} or
{cmd:netcalc_fratio}. The output
frames carry the variables under the default names whatever the data
called them, and so do the rows a refusal lists.

{phang}
{opt replace} writes over a network of the same name. Without it, a
name that either output frame already holds is refused before anything
is computed. With it, the name is cleared from both frames, the
{it:newvar}{cmd:_fratio} column with it, and the network is written
anew; the clearing comes only after every check of the call has passed,
so a refused call leaves the old network in place.

{phang}
{opt debug} displays the intermediate quantities of the template and a
summary of the calculated network. Use it to see why a value is not
what you expected.


{marker input}{...}
{title:Input data}

{pstd}
The data in memory must be in long form, one observation per directed
edge and period. Without a feature it must hold, under these names or
under the names given in {cmd:period()}, {cmd:source()},
{cmd:target()} and {cmd:value()}:

{p2colset 9 30 32 2}{...}
{p2col :{cmd:year}}period identifier{p_end}
{p2col :{cmd:source}}node the edge leaves{p_end}
{p2col :{cmd:target}}node the edge enters{p_end}
{p2col :{cmd:source_value}}quantity measured at {cmd:source}{p_end}
{p2col :{cmd:target_value}}quantity measured at {cmd:target}{p_end}
{p2colreset}{...}

{pstd}
Under {cmd:flow}, both value columns describe the edge itself:
{cmd:source_value} is the quantity of the edge i,j as recorded at i,
and {cmd:target_value} the quantity of the same edge as recorded at j,
as with exports declared by the exporter and imports declared by the
importer. Where a single record exists, the same figure goes into both
columns. {cmd:outflow} reads the first and {cmd:inflow} the second.

{pstd}
The data must be the complete panel of their rows: a row for every
period, every ordered pair i,j with j != i of the nodes, and, with
{cmd:subnet(multi)}, every level of the feature. The periods, the nodes
and the levels are those the data name: every value of {cmd:year},
every value that appears as {cmd:source} or {cmd:target}, and every
value of the feature. Under {cmd:interaction} and {cmd:attribute} each
node carries one value, and under {cmd:flow} each edge carries its
own. A flow or an interaction that did not happen is a row with value
zero, which the data supply: the command fills in no row and no value.
Data with a row
missing are refused, and the command lists the missing rows and their
number in each period.

{pstd}
With {cmd:subnet(multi)} the panel holds one observation per period,
subnet and directed edge, and carries two columns more, under these
names or the names given in {cmd:size()}:

{p2colset 9 30 32 2}{...}
{p2col :{cmd:year}}period identifier{p_end}
{p2col :{it:feature}}the variable named in {cmd:feature()}, which
splits each node into subnets{p_end}
{p2col :{cmd:source}}node the edge leaves{p_end}
{p2col :{cmd:target}}node the edge enters{p_end}
{p2col :{cmd:source_size}}what the subnet weighs at {cmd:source}{p_end}
{p2col :{cmd:source_value}}quantity measured at {cmd:source}{p_end}
{p2col :{cmd:target_size}}what the subnet weighs at {cmd:target}{p_end}
{p2col :{cmd:target_value}}quantity measured at {cmd:target}{p_end}
{p2colreset}{...}

{pstd}
{cmd:size} is what the subnet weighs at that node: the people born in
a given province who live there, the passengers carried by a given mode,
whatever the subnets are counted in. It is read as a ratio, the subnet
over the node, so the units it is counted in do not matter and the
command writes that ratio out beside the weights. {cmd:value} is the
quantity the network is about. What belongs in {cmd:value} follows from
the feature: splitting an edge by transport mode makes a distance in
kilometres meaningless and a fare or a tonnage meaningful.

{pstd}
A figure that describes a node is repeated on every row that names the
node, as {cmd:source_}{it:...} on the rows the node leaves and as
{cmd:target_}{it:...} on the rows it enters, and the rows must agree:
under {cmd:interaction} the size and the value of a subnet at its node,
the template reading the size once for each subnet, and under
{cmd:attribute} the level of the node. The command checks it. Data in
which the figure differs between the rows of a node, or between the rows
that name the node as source and those that name it as target, by more
than floating-point error, a relative difference of 1e-12, are refused,
and the cases are listed with the figures that differ. Under
{cmd:flow} the values describe the edge, and {cmd:size} is added up
over the rows of the subnet, so it may describe the edge and change
from one target to the next, as the migrants of one group sent along
each edge would, or describe the node and be the same on every row of a
complete mesh; nothing is compared there.

{pstd}
{cmd:source} and {cmd:target} may be string or numeric, both of one
kind. The frames are keyed on the two node columns, so a node name may
hold whatever it likes, an underscore included, and a numeric
identifier works as it is. {cmd:edge_id}, the label of the ordered
pair that the frames carry beside the node columns, is built from the
two values joined by an underscore; for numeric nodes it holds the
numbers.


{marker templates}{...}
{title:Templates}

{dlgtab:interaction}

{pstd}
{cmd:type(interaction)} requires {cmd:subnet(multi)}: its weight is
defined inside a subnet, the same subnet at the two nodes, so the call
names the feature that defines the subnets. A feature with a single
level gives a network with one subnet, and {cmd:subnet(single)} is kept
for data without a feature. The weight is the
quantity of the subnet at the target over its quantity at every node
but the source, read from {cmd:value}:

{p 8 8 2}
ω(ij,X) = v(j,X) / sum over k != i of v(k,X)

{pstd}
How much of the quantity the subnet carries, outside the source node,
sits at the target. A subnet is a network of its own and its weights
add up to one. {cmd:size} does not enter that weight; it enters where
the subnets are put back together, giving each its ratio in
the copy written to {cmd:networks_single}.

{dlgtab:flow}

{pstd}
{cmd:type(flow)} accepts either scope. Under {cmd:subnet(single)} the
weight is the quantity of the edge over the total that leaves its node
in that period:

{p 8 8 2}
w(ij) = v(ij) / sum over k != i of v(ik)

{pstd}
Under {cmd:subnet(multi)} the same division is made inside the subnet, so
a subnet is a network in its own right and its weights add up to one on
their own:

{p 8 8 2}
w(ij,X) = v(ij,X) / sum over k != i of v(ik,X)

{pstd}
Under {cmd:direction(inflow)} the weight is anchored at the target and
read from {cmd:target_value}, u below:

{p 8 8 2}
w(ij) = u(ij) / sum over k != j of u(kj)

{pstd}
{cmd:size} does not enter that weight. It enters where the subnets are
put back together: each subnet is scaled by its ratio at the node before
the copy in {cmd:networks_single} is added up.

{pstd}
Use it for quantities that travel along the edge: migration, trade,
capital.

{dlgtab:attribute}

{pstd}
{cmd:type(attribute)} takes {cmd:subnet(single)}: an attribute
describes the node and has no subnets. The value is the log ratio of
the two node values:

{p 8 8 2}
w(ij) = ln[A(j) / A(i)]     under {cmd:direction(outflow)}

{pstd}
Where the levels are recorded for groups within a node, reduce them to
the node before the call, for instance as a mean weighted by the size
of each group, and pass the node level.

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
{p2col :{cmd:networks_single}}keyed on {cmd:year}, {cmd:source} and
{cmd:target}{p_end}
{p2col :{cmd:networks_multi}}keyed on {cmd:year}, {cmd:feature},
{cmd:source} and {cmd:target}{p_end}
{p2colreset}{...}

{pstd}
The two names are reserved for this output: a frame of either name is
taken to hold the output of earlier calls. To keep two panels apart in
one session, rename the frames of the first with {help frame rename}
before building the second.

{pstd}
Beside the key, each frame carries {cmd:edge_id}, {cmd:source} and
{cmd:target} joined by an underscore: a label of the ordered pair, kept
for convenience and for the do-files that use it, and not the key of
the join.
Every call adds the network, named by {cmd:name()}, to the frame or
frames it writes, and a {cmd:subnet(multi)} call writes two columns
into {cmd:networks_multi}: the network and, beside it,
{it:newvar}{cmd:_fratio}.

{p2colset 9 34 36 2}{...}
{p2col :{cmd:subnet(single)}}{cmd:networks_single}{p_end}
{p2col :{cmd:interaction}, {cmd:subnet(multi)}}both{p_end}
{p2col :{cmd:flow}, {cmd:subnet(multi)}}both{p_end}
{p2colreset}{...}

{pstd}
A frame is a panel of edges, and every network in it is a column of
that panel. A call therefore joins a frame only with the rows the frame
holds: the same periods and edges and, in {cmd:networks_multi}, the
same subnets, split by the same feature: the frame records the name
of the variable named in {cmd:feature()}, and a call that names another
variable is refused, even where the levels of the two coincide; it
cannot tell apart two features that share both a name and their
levels. Nothing is
filled in on either side. A call with a row
the frame lacks, or without a row the frame holds, is refused, and the
rows on either side are listed. That is what happens when the input
files name different nodes or periods, or when two multi-subnet
networks are split by different features.

{pstd}
Whatever could stop a join, a network whose rows differ from those of
the frame, a feature of another name, a key that is a string on one
side and numeric on the other, and a variable named {cmd:_merge} in the
frame, is checked
against every frame a call writes before the first of them changes, so
a call writes both frames or neither. A name a frame already holds is
refused before anything is computed, unless {cmd:replace} is specified,
and then it is cleared from both frames only once every check has
passed.

{pstd}
A {cmd:subnet(multi)} call writes a second column into
{cmd:networks_multi}, named after the network with {cmd:_fratio} added:
the ratio of the subnet within the feature at its node, which is what
the {cmd:size} columns are read as. It is a number between zero and one
and the ratios of a node add up to one over the subnets, so a regression
run one subnet at a time has both the weights of that subnet and the
ratio of the subnet at its node. Each call reads the sizes of its own input,
so two networks split the same way carry a column each and need not
weigh their subnets alike.

{pstd}
The copy in {cmd:networks_single} adds the subnet weights up after each
has been scaled by the ratio its {cmd:size} gives it at the node. A
subnet of {cmd:interaction} or {cmd:flow} is a network of its own,
whose weights add up to one; the ratios of a node add up to one as
well, so the copy is the weight of the edge in the node as a whole.

{pstd}
A network read at the two resolutions is not the same calculation. A
single-subnet network computed from single-subnet data and the
single-subnet copy of a {cmd:subnet(multi)} call answer different
questions and will not agree in general.


{marker examples}{...}
{title:Examples}

{pstd}
The examples read the {cmd:.csv} files that {cmd:generate_test_data.do},
distributed with the package, builds in the directory it is run from,
and run from that directory. The files are not distributed themselves:
the two multi-subnet files hold 3,149,280 rows each. Where a file is
split into subnets, the variable {cmd:feature} holds the node people
were born in.

{pstd}Social connection by birthplace, one subnet per birthplace{p_end}
{phang2}{cmd:. import delimited test_interaction_multi.csv, clear}{p_end}
{phang2}{cmd:. network_calc, type(interaction) subnet(multi)}{break}
{cmd:          feature(feature) name(bplace)}{p_end}

{pstd}Migration split by the same subnets, and the ratio each subnet
holds at its node, which the call leaves in {cmd:mig_out_fratio}{p_end}
{phang2}{cmd:. import delimited test_flow_multi.csv, clear}{p_end}
{phang2}{cmd:. network_calc, type(flow) subnet(multi)}{break}
{cmd:          feature(feature) name(mig_out)}{p_end}

{pstd}The same flows seen from the receiving node{p_end}
{phang2}{cmd:. network_calc, type(flow) subnet(multi)}{break}
{cmd:          feature(feature) direction(inflow) name(mig_in)}{p_end}

{pstd}The same migration pooled over the subnets, one network without
a feature; it differs from the single-subnet copy of {cmd:mig_out},
which weighs the subnets by their size{p_end}
{phang2}{cmd:. import delimited test_flow_single.csv, clear}{p_end}
{phang2}{cmd:. network_calc, type(flow) subnet(single) name(mig_pool)}{p_end}

{pstd}The schooling gap between the two nodes of each edge{p_end}
{phang2}{cmd:. import delimited test_attribute_single.csv, clear}{p_end}
{phang2}{cmd:. network_calc, type(attribute) subnet(single) name(sch)}{p_end}

{pstd}The same data under other variable names, and a network written
anew under a name the frame holds{p_end}
{phang2}{cmd:. rename (year source target) (yr orig dest)}{p_end}
{phang2}{cmd:. network_calc, type(attribute) subnet(single) name(sch)}{break}
{cmd:          period(yr) source(orig) target(dest) replace}{p_end}

{pstd}Estimating on the edge panel the calls have built. The
estimation lies outside {cmd:network_calc}, and so does the outcome: it
comes from a file of its own, {cmd:test_outcome.csv}, and is linked to
the panel on its key.{p_end}
{phang2}{cmd:. frame create outcome}{p_end}
{phang2}{cmd:. frame outcome: import delimited test_outcome.csv, clear}{p_end}
{phang2}{cmd:. frame change networks_single}{p_end}
{phang2}{cmd:. frlink 1:1 year source target, frame(outcome)}{p_end}
{phang2}{cmd:. frget y, from(outcome)}{p_end}
{phang2}{cmd:. egen pair = group(source target)}{p_end}
{phang2}{cmd:. encode source, generate(src) label(node)}{p_end}
{phang2}{cmd:. encode target, generate(tgt) label(node)}{p_end}
{phang2}{cmd:. reghdfe y mig_out sch, absorb(pair year) vce(cluster src tgt)}{p_end}

{pstd}
An attribute value is the difference of a target-period and a
source-period term, so source-period and target-period fixed effects
together would absorb {cmd:sch} entirely; the example absorbs the
ordered pair and the period instead. Edges that share a node are not
independent, so the standard errors are clustered on the source and on
the target; {cmd:example_session.do} adds the node jackknife beside
them.


{marker results}{...}
{title:Stored results}

{pstd}
{cmd:network_calc} stores the following in {cmd:r()}:

{synoptset 24 tabbed}{...}
{p2col 5 24 28 2: Scalars}{p_end}
{synopt:{cmd:r(n_edges)}}number of rows calculated; under
{cmd:subnet(multi)} a row is the edge of one subnet{p_end}
{synopt:{cmd:r(n_pairs)}}number of distinct edges, ordered pairs within
a period{p_end}
{synopt:{cmd:r(mean_weight)}}mean of the calculated variable; on a
complete mesh it is zero under {cmd:attribute} and, where no total is
zero, one over the number of alternatives under {cmd:interaction} and
{cmd:flow}, so it guards against gross errors only{p_end}
{synopt:{cmd:r(n_zero_totals)}}number of totals that came to zero, one
for each node and period, or node, period and subnet, whose weights
were written as zero for want of a total{p_end}
{synopt:{cmd:r(n_zero_sizes)}}number of nodes and periods whose sizes
add up to zero, so that the ratios of their subnets were written as
zero; under {cmd:subnet(multi)}{p_end}

{p2col 5 24 28 2: Macros}{p_end}
{synopt:{cmd:r(network_name)}}name given in {cmd:name()}{p_end}
{synopt:{cmd:r(network_type)}}template given in {cmd:type()}{p_end}
{synopt:{cmd:r(subnet_type)}}scope given in {cmd:subnet()}{p_end}
{p2colreset}{...}


{marker chars}{...}
{title:Characteristics}

{pstd}
Each network column, the variable named in {cmd:name()}, records the
template that produced it in the variable characteristic
{cmd:netcalc_type}, which {cmd:char list} displays: {cmd:interaction},
{cmd:flow} or {cmd:attribute}. The {it:_fratio} columns carry none. In
{cmd:networks_multi}, the key variable {cmd:feature} carries the
characteristic {cmd:netcalc_feature}, the name of the variable the frame
is split by, which a call split by another feature is checked against.


{marker author}{...}
{title:Author}

{pstd}
Necmi Talay{break}
{browse "mailto:aggilitas@gmail.com":aggilitas@gmail.com}{break}
{browse "https://github.com/aggilitas/stata-networks":stata-networks}


{marker citation}{...}
{title:Citation}

{pstd}
If you use {cmd:network_calc}, please cite the article that sets out
the framework it implements:

{phang}
Talay, N., H. Acaroglu, A. Gunal, and F. P. Garcia Marquez. 2026.
Algebraic invariant multilayer-network edge regression: Multi-source
data fusion with macro-shock immunity. {it:Knowledge-Based Systems}
352: 117007. {browse "https://doi.org/10.1016/j.knosys.2026.117007"}


{marker alsosee}{...}
{title:Also see}

{psee}
Online: {help frames}, {help reghdfe} (if installed)
{p_end}

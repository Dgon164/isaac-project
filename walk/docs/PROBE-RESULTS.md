# What Ergo can do — capability probe

Four things worth knowing, all run, not reasoned about. Knowledge base is
`probe.ergo`, queries are `qp.txt`.

## 1. Defaults with exceptions

A rule at the class level, an exception at the member level, one line of
priority. Neither rule is deleted.

    @{default_metals_conduct}
    ?X[conducts_heat -> high] :- ?X : metal.

    @{anodized_exception}
    \neg ?X[conducts_heat -> high] :- ?X : metal, ?X[surface -> anodized].

    \overrides(anodized_exception, default_metals_conduct).

Result:

    steel[conducts_heat -> high].            Yes
    aluminum[conducts_heat -> high].         Yes
    alum_part_7[conducts_heat -> high].      No
    \neg alum_part_7[conducts_heat -> high]. Yes

The general rule still applies to everything it should. The one member with a
reason to differ goes the other way. Nothing had to be restated per member.

## 2. Cycles do not hang

    depends(bracket, fastener).
    depends(fastener, bracket).    // cycle
    depends(bracket, subframe).    // second cycle

    reaches(?A,?B) :- depends(?A,?B).
    reaches(?A,?B) :- depends(?A,?C), reaches(?C,?B).

    reaches(assembly, ?X).  ->  bracket, fastener, subframe   (1 ms)

Plain Prolog runs forever on this. XSB records what it has already asked and
reuses the answer, so a cyclic dependency graph is just a normal query. Isaac's
maps will have cycles in them, so this matters more than it looks.

## 3. Meta-discovery — finding axes that were never asked

No slot is named by hand anywhere in this rule:

    has_slot(?N,?S)   :- ?N[?S -> ?_].
    sibling(?A,?B)    :- ?A : ?C, ?B : ?C, ?A \= ?B.

    missing_axis(?Node,?Slot) :-
        sibling(?Node,?Other),
        has_slot(?Other,?Slot),
        \naf has_slot(?Node,?Slot).

Result — five gaps found from uneven coverage across three nodes:

    alum_part_7 / density_class
    alum_part_7 / magnetic
    aluminum    / magnetic
    aluminum    / surface
    steel       / surface

This is question generation. Ergo is reporting what it has not been told, by
comparing a node against its siblings. That is the "find the undetected missing
parts" requirement running on a real engine in 6 ms.

Note the rule is indiscriminate: it reports `surface` as missing for steel and
aluminum because one sibling happens to have it. Every gap is reported whether
or not it is worth asking about. Some filter has to decide which generated
questions matter — which looks like where the 0 value earns its keep, since a
generated question Isaac has already judged irrelevant is exactly a 0.

## 4. Grouped aggregates

    coverage(?N,?Count) :- ?Count = count{?S[?N] | has_slot(?N,?S)}.

    steel 3, aluminum 2, alum_part_7 2

The `[?N]` inside the braces is the grouping key. Without it the count runs
across everything and returns one global number, which is what my first
attempt did.

## Gotcha that cost two runs

`@{tag}` and `@!{tag}` are not the same. The bang form makes a rule strict.
With `@!` on both rules, the default AND the exception both held at once —
`alum_part_7[conducts_heat -> high]` and its negation were both Yes, a live
contradiction sitting in the store with no complaint from the engine.
Changing both tags to `@{...}` made the priority take effect.

Worth knowing because the failure is silent. Nothing errors; you just get
answers that contradict each other. If the transcriber ever emits the wrong
tag form, the store quietly stops meaning anything.

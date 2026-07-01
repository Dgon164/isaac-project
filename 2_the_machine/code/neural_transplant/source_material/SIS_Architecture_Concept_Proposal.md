# SIS Architecture — Concept Proposal

**Status:** Proposal for review and research. Not approved.
**Date:** April 21, 2026
**Context:** This emerged from rethinking the system as a processor rather than a database. The key insight: nodes are data packets that don't do anything. You need a structure to organize them and an engine to act on them. These are two separate concerns.

---

## THE TWO LAYERS

### Layer 1: Structure — How information is organized

This is the filing system. It holds things, lets you find things, lets you reference one thing from another. It has no behavior. It's a warehouse with a good labeling system.

### Layer 2: Execution — What happens to the information

This is the engine that reads instructions and acts on them. It operates on whatever the structure layer holds. It can do anything — math, logic, comparison, lookup, creation, validation — as long as the structure gives it something to work with.

The separation is absolute. Structure never executes. Execution never stores. Structure is the noun. Execution is the verb.

---

## LAYER 1: THE STRUCTURE

### The Train — A List That Grows

The fundamental working unit is a list. Call it a train. It's an ordered sequence of items (cars) that grows by appending. New results go on the end. Old items stay where they are unless explicitly overwritten.

The train is the working memory. Everything the system is currently thinking about is in the train. When execution finishes, the train is the complete record of what happened — every input, every intermediate result, every step.

A train can be any length. There's no fixed number of slots. Start with two cars, end with two hundred. The list grows as the computation needs it to.

### The Car — One Item in the List

A car is one entry in the train. It holds one of two things:

**A value** — a piece of data. An integer, a node reference, a dim pattern, a weight. Something that just sits there and can be read.

**A procedure** — a sequence of instructions. Something that tells the execution layer what to do. Take these arguments, do these steps, return a result.

The car doesn't know which kind it is in any deep sense. It's just data either way. The difference is what the execution layer does when it reads it — if it's a value, use it. If it's a procedure, follow it.

Every car has a position in the list (its address within the train). Any other car can reference it by that position.

### Selection — Pointing at Cars

Before the execution layer can do anything, it needs to know which cars to work with. Selection is how you say "these ones."

Selection is just a pointer (or set of pointers) into the train. "Car 0 and car 3 are selected." Now the next operation knows what to work on.

Selection can be:

- **By position** — "car 4." Direct. You know exactly where it is.
- **By content** — "the car whose value is 5." A search. Slower, but necessary when you don't know the position.
- **By dims** — "the car with the {additive, operator} dims active." Semantic selection. This is where the meaning plane connects to the structure. You're choosing based on what something IS, not where it sits.

### Appending — Adding New Cars

Every operation that produces a result creates a new car at the end of the train. ADD two values? New car at the end holds the sum. Run a comparison? New car at the end holds the result.

Default behavior is always append. The train grows. Nothing is destroyed. If you need to overwrite (put a new value in an existing car's position), that's an explicit instruction, not the default.

This means the train is a full trace. You can always look backward and see what happened. Car 47 was produced by ADDing car 12 and car 31. That lineage is implicit in the instruction sequence that built it.

### Persistence — When a Train Becomes a Node

A train is ephemeral by default. It exists while the system is working on a problem, then it's done.

But if a train (or part of a train) turns out to be useful — a procedure that keeps producing correct results, a pattern that keeps appearing — it can be persisted as a node in the permanent graph. The procedure car becomes a procedure node. Now it's callable from any future train, by any future problem.

This is how the system creates subroutines. Run a sequence. It works. Collapse it into a procedure car. Persist it as a node. Done. It's now a reusable function.

---

## LAYER 2: THE EXECUTION

### The Engine

A loop that reads the current instruction, does what it says, and moves to the next one. It has:

- **A position counter** — where in the current procedure am I? Advances by one unless told otherwise.
- **A return stack** — where to go back when a sub-procedure finishes. Push on call, pop on return.
- **Access to the train** — it can read any car, append new cars, and select cars for operations.

That's all the state the engine carries. Everything else is in the train.

### Instructions

An instruction says: what to do, what to do it with, and where to put the result.

The instruction set is open-ended. It starts with a minimal set but can grow as the system discovers new operations and persists them as procedure nodes. The categories are:

**Data movement:**
- SELECT — point at one or more cars in the train.
- APPEND — add a new car to the end of the train with a given value.
- OVERWRITE — replace the contents of a specific car (explicit, not default).

**Primitives — the computational floor:**
- ADD — sum two selected values, append result.
- NEG — flip the sign of a selected value, append result.
- AND — logical AND on two selected values, append result.
- OR — logical OR on two selected values, append result.
- NOT — logical NOT on a selected value, append result.
- EQ — equality check on two selected values, append result (1 or 0).

These six guarantee computational completeness — anything a CPU can do, you can build from these. But they're not sacred. They're just the starting vocabulary.

**Control flow:**
- JUMP — move the position counter to a specific instruction.
- JUMP_IF — move the position counter only if a selected car is nonzero.
- CALL — save current position, start executing a procedure car (or procedure node).
- RETURN — pop the return stack and go back. If stack is empty, execution is done.

**System operations (the open-ended part):**
- COMPARE — run the Comparator on two selected cars. Produces shared/divergent/absent analysis. Appends result.
- CHECK — validate that a value doesn't violate a constraint. Appends pass/fail.
- LOOKUP — navigate the dim trie to find a node. Appends the node reference.
- CREATE — make a new node in the permanent graph. Appends the new node's address.
- LINK — create a pointer between two nodes.

These aren't primitives. They're higher-level operations that are themselves built from primitives (or from native code, when performance demands it). The list grows as the system needs new verbs.

### How an Instruction Reads

In natural language, an instruction reads like a sentence:

```
"Select car 1 and car 2, ADD them."
→ Result appears as new car 3.

"Select car 3, check if it violates constraint X."
→ Result (pass/fail) appears as new car 4.

"Select car 4, if nonzero jump to instruction 8."
→ Position counter moves to 8 (or doesn't).

"Call the procedure in car 7 with car 1 and car 3 as arguments."
→ Engine saves its place, goes to execute that procedure, comes back.
```

### How a Procedure Reads

A procedure is just a list of instructions with a contract: here's what I expect as arguments, here's what I'll return.

```
Procedure: subtract
  Takes: two selected cars (A and B)
  Steps:
    NEG B → new car (this is -B)
    ADD A and -B → new car (this is A - B)
  Returns: the last new car

Procedure: is_greater_than
  Takes: two selected cars (A and B)
  Steps:
    CALL subtract with A and B → new car (difference)
    JUMP_IF difference is nonzero → "yes" path
    ... handle equal case ...
    ... handle greater case ...
  Returns: 1 or 0

Procedure: find_missing_operand
  Takes: a train representing "5 + _ = 8"
  Steps:
    SELECT the result car (8) and the known operand car (5)
    CALL subtract with result and known → new car (3)
    CHECK: is 3 ≥ 0? (constraint: operands must be non-negative)
    CHECK: is 3 < 8? (constraint: operand must be less than result for addition)
  Returns: the answer car (3)
```

The last example shows the constraint reasoning you described — the system isn't just blindly computing. It's checking that its answer satisfies the logical relationships. The constraints narrow the space of valid answers the same way dims narrow the space of valid concepts.

---

## THE THREE PLANES ON A NODE

Every node in the permanent graph has three faces. These aren't separate storage systems — they're three ways of looking at the same node.

### Title — What it's called

The label. "5", "+", "cat", "subtract". A lookup key. Title is how you find the node when you have a name. Title has no semantic content and no operational meaning.

### Function — What it does

The procedure (if any). If this node represents an operation, its function face holds the instruction list. "+" has a function face that says: take two arguments, ADD them, return the result.

Not every node has a function face. "5" is just a value — it doesn't do anything. But "+" is both a value (the symbol) and a function (the operation). "is_greater_than" is a procedure node — its entire purpose is its function face.

When the execution layer hits a CALL to this node, it reads the function face and executes the procedure it finds there.

### Meaning — What it represents

The semantic dims. This is what makes "cat" different from "dog." This is how the system knows that "bank" by a river and "bank" with money are different concepts on the same node.

Meaning is what the SELECT-by-dims operation uses. When the execution layer needs to choose between cars based on what they represent (not where they sit or what they're called), it reads the meaning face.

---

## HOW IT ALL CONNECTS

A problem arrives: "5 + 3 = _"

**Structure layer builds the train:**
- Car 0: value 5 (from node "5")
- Car 1: operator + (from node "+")
- Car 2: value 3 (from node "3")
- Car 3: equals sign (from node "=")
- Car 4: blank (unknown — to be filled)

**Execution layer decodes:**
- SELECT car 1 (the operator). Read its dims. It has {operator, additive}. These dims navigate to the relevant procedure node.
- SELECT car 4 (the blank). Its position relative to the other cars tells the system what role is missing — in this case, the result.

**Execution layer runs the procedure:**
- The procedure node for "additive, result missing" says: SELECT the two operands, CALL ADD, RETURN the result.
- SELECT car 0 (value 5) and car 2 (value 3).
- ADD → new car 5 (value 8).
- RETURN. Answer is car 5.

**If the blank were in a different position** — "5 + _ = 8" — the decode step would navigate to a different procedure (or a different branch of the same procedure): SELECT the result and the known operand, CALL SUBTRACT, CHECK constraints, RETURN.

The structure didn't change. The train is still a list of cars. The execution layer just followed different instructions because the dims pointed to a different procedure.

---

## HOW SUBROUTINES GET BORN

1. A problem arrives that doesn't match any existing procedure node.
2. The system tries paths — sequences of operations on the train. (The GPU can try many paths in parallel.)
3. Some paths produce a result that passes the grading check. Most don't.
4. Across multiple similar problems, a pattern emerges: the surviving paths share the same sequence of operations.
5. That shared sequence gets collapsed into a procedure car.
6. The procedure car gets persisted as a new node in the graph with a function face.
7. Its meaning face gets the dims that identify when it applies — discovered from the structural signature of the problems it solved.
8. Next time a problem with those dims appears, the decode step navigates directly to this node. No more brute force.

The system wrote its own function. The function is a node. The node is callable. It was discovered, not designed.

---

## WHAT'S STILL UNDEFINED

This proposal covers the conceptual model. It does NOT define:

- **The exact format of a car.** What does a car look like in memory? How big is it? How does it distinguish value from procedure?
- **The exact format of an instruction.** How is "SELECT car 1 and car 2, ADD them" encoded? Bit layout? Integer codes?
- **How SELECT-by-dims works mechanically.** Saying "select the car with additive dims" is easy in English. How does the engine actually do that search?
- **How the decode step navigates from dims to a procedure node.** The trie structure is described conceptually but not mechanically.
- **How the grading loop identifies patterns across surviving paths.** This is the subroutine discovery mechanism. It exists conceptually (it's the word search applied to execution paths) but isn't specified mechanically.
- **Memory management.** Trains grow. When do they get cleaned up? What stays, what gets discarded?
- **Concurrency.** Can multiple trains exist at once? How do they share the permanent graph without stepping on each other?

These are all implementation questions. They matter, but they're downstream of whether the conceptual model is right.

---

## SUMMARY

Two layers. Structure organizes. Execution acts. A train is a growing list of cars. A car is a value or a procedure. Selection points at cars. Operations produce new cars at the end. The engine reads instructions and follows them. Procedures are just cars that contain instruction lists. Nodes in the permanent graph have three faces: title (name), function (instructions), meaning (dims). Subroutines get discovered by running many paths, keeping what works, finding the pattern, and saving it as a new callable node.

---

*This is a concept proposal. It captures the ideas as discussed. Everything is open to correction, refinement, or rejection. Nothing here is approved for implementation.*

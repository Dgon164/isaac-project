# Intellon xb.4 — Tool Curriculum

**Purpose:** Test sheets for every primitive. The system verifies each example, discovers the rule, then proves understanding with self-generated tests. 10 correct novel predictions in a row = trusted.

**Learning order matters.** Each level uses tools from the previous level to self-check.

---

## Level 1: Comparison (Foundation)

### EQ — Are these the same?
```
(EQ 1 1) → true           (EQ 1 2) → false
(EQ 0 0) → true           (EQ 5 3) → false
(EQ -1 -1) → true         (EQ -1 1) → false
(EQ "a" "a") → true       (EQ "a" "b") → false
(EQ true true) → true     (EQ true false) → false
```
**Outputs:** true, false
**Edge:** (EQ 0 false) → false — different types are not equal

### NEQ — Are these different?
```
(NEQ 1 2) → true          (NEQ 1 1) → false
(NEQ 5 3) → true          (NEQ 0 0) → false
(NEQ "a" "b") → true      (NEQ "a" "a") → false
(NEQ true false) → true   (NEQ true true) → false
```
**Outputs:** true, false
**Rule:** Opposite of EQ. Always.

---

## Level 2: Boolean States

### NOT — Flip it
```
(NOT true) → false
(NOT false) → true
```
**Outputs:** true, false
**Only 2 cases.** Both must pass. Self-test: repeat and verify consistency.

### AND — Both must be true
```
(AND true true) → true
(AND true false) → false
(AND false true) → false
(AND false false) → false
```
**Outputs:** true, false
**Only true when ALL inputs are true.**

### OR — At least one must be true
```
(OR true true) → true
(OR true false) → true
(OR false true) → true
(OR false false) → false
```
**Outputs:** true, false
**Only false when ALL inputs are false.**

### XOR — Exactly one, not both
```
(XOR true true) → false
(XOR true false) → true
(XOR false true) → true
(XOR false false) → false
```
**Outputs:** true, false
**True when inputs DIFFER. Different from NEQ because XOR is strictly boolean.**

---

## Level 3: Ordered Comparison

### GT — Is the first bigger?
```
(GT 5 3) → true           (GT 3 5) → false
(GT 5 5) → false          (GT 0 -1) → true
(GT -1 0) → false         (GT 10 9) → true
(GT 1 1) → false          (GT 100 1) → true
```

### LT — Is the first smaller?
```
(LT 3 5) → true           (LT 5 3) → false
(LT 5 5) → false          (LT -1 0) → true
(LT 0 -1) → false         (LT 1 10) → true
```

### GTE — Bigger or same?
```
(GTE 5 3) → true          (GTE 3 5) → false
(GTE 5 5) → true          (GTE 0 0) → true
(GTE -1 0) → false        (GTE 10 1) → true
```

### LTE — Smaller or same?
```
(LTE 3 5) → true          (LTE 5 3) → false
(LTE 5 5) → true          (LTE 0 0) → true
(LTE 0 -1) → false        (LTE 1 10) → true
```

---

## Level 4: Basic Arithmetic

### ADD — Combine quantities
```
(ADD 1 2) → 3             (ADD 0 5) → 5
(ADD 5 5) → 10            (ADD -1 3) → 2
(ADD 2 3) → 5             (ADD 0 0) → 0
(ADD 7 1) → 8             (ADD -3 -2) → -5
(ADD 1 2 3) → 6           (ADD 10 -10) → 0
```
**Variadic:** works with 1, 2, 3+ inputs.
**Edge:** (ADD 0 x) → x. Zero changes nothing.

### SUB — Remove quantities
```
(SUB 5 3) → 2             (SUB 3 5) → -2
(SUB 10 0) → 10           (SUB 0 5) → -5
(SUB 5 5) → 0             (SUB -1 -3) → 2
(SUB 7 1) → 6             (SUB 100 1) → 99
```
**NOT commutative:** (SUB 5 3) ≠ (SUB 3 5). Order matters.
**Edge:** (SUB x x) → 0. Anything minus itself is zero.

---

## Level 5: More Arithmetic

### MUL — Multiply
```
(MUL 2 3) → 6             (MUL 5 0) → 0
(MUL 4 4) → 16            (MUL -1 5) → -5
(MUL 1 7) → 7             (MUL -2 -3) → 6
(MUL 3 3) → 9             (MUL 10 10) → 100
(MUL 2 3 4) → 24          (MUL 0 0) → 0
```
**Edge:** (MUL 1 x) → x. One changes nothing. (MUL 0 x) → 0. Zero kills everything.

### DIV — Divide
```
(DIV 10 2) → 5            (DIV 9 3) → 3
(DIV 7 2) → 3.5           (DIV 1 4) → 0.25
(DIV 0 5) → 0             (DIV -6 3) → -2
(DIV 100 10) → 10         (DIV 5 0) → null
```
**NOT commutative.** (DIV 5 0) → null. Cannot divide by zero.

### MOD — Remainder after division
```
(MOD 10 3) → 1            (MOD 9 3) → 0
(MOD 7 2) → 1             (MOD 5 5) → 0
(MOD 8 3) → 2             (MOD 0 5) → 0
(MOD 13 4) → 1            (MOD 5 0) → null
```
**Edge:** (MOD x x) → 0. (MOD 0 x) → 0.

### POW — Power (exponent)
```
(POW 2 3) → 8             (POW 3 2) → 9
(POW 5 0) → 1             (POW 0 5) → 0
(POW 2 10) → 1024         (POW 10 2) → 100
(POW 1 100) → 1           (POW -1 2) → 1
```
**NOT commutative.** (POW x 0) → 1 always. (POW 0 x) → 0 always.

---

## Level 6: Single-Number Transforms

### NEG — Flip the sign
```
(NEG 5) → -5              (NEG -5) → 5
(NEG 0) → 0               (NEG 1) → -1
(NEG -1) → 1              (NEG 100) → -100
```

### ABS — Remove the sign (always positive)
```
(ABS 5) → 5               (ABS -5) → 5
(ABS 0) → 0               (ABS -1) → 1
(ABS 1) → 1               (ABS -100) → 100
```

### SIGN — Which direction? (-1, 0, or 1)
```
(SIGN 5) → 1              (SIGN -5) → -1
(SIGN 0) → 0              (SIGN 100) → 1
(SIGN -1) → -1            (SIGN 1) → 1
```
**Only 3 possible outputs:** -1, 0, 1

### MIN — Smaller of two
```
(MIN 3 5) → 3             (MIN 5 3) → 3
(MIN -1 0) → -1           (MIN 5 5) → 5
(MIN 0 0) → 0             (MIN 10 1) → 1
```

### MAX — Larger of two
```
(MAX 3 5) → 5             (MAX 5 3) → 5
(MAX -1 0) → 0            (MAX 5 5) → 5
(MAX 0 0) → 0             (MAX 10 1) → 10
```

### FLOOR — Round down
```
(FLOOR 3.7) → 3           (FLOOR 3.2) → 3
(FLOOR -1.5) → -2         (FLOOR 5) → 5
(FLOOR 0.9) → 0           (FLOOR -0.1) → -1
```

### CEIL — Round up
```
(CEIL 3.2) → 4            (CEIL 3.7) → 4
(CEIL -1.5) → -1          (CEIL 5) → 5
(CEIL 0.1) → 1            (CEIL -0.9) → 0
```

### ROUND — Round to nearest
```
(ROUND 3.2) → 3           (ROUND 3.7) → 4
(ROUND 3.5) → 4           (ROUND -1.5) → -1
(ROUND 5) → 5             (ROUND 0.4) → 0
```

---

## Level 7: String Operations

### S_LEN — How many characters?
```
(S_LEN "hello") → 5       (S_LEN "a") → 1
(S_LEN "") → 0            (S_LEN "cat") → 3
(S_LEN "abcdef") → 6      (S_LEN " ") → 1
```

### S_UPPER — Make all capitals
```
(S_UPPER "hello") → "HELLO"    (S_UPPER "cat") → "CAT"
(S_UPPER "ABC") → "ABC"        (S_UPPER "a") → "A"
(S_UPPER "") → ""              (S_UPPER "Hello") → "HELLO"
```

### S_LOWER — Make all lowercase
```
(S_LOWER "HELLO") → "hello"    (S_LOWER "CAT") → "cat"
(S_LOWER "abc") → "abc"        (S_LOWER "A") → "a"
(S_LOWER "") → ""              (S_LOWER "Hello") → "hello"
```

### S_REV — Reverse the characters
```
(S_REV "hello") → "olleh"      (S_REV "abc") → "cba"
(S_REV "a") → "a"              (S_REV "") → ""
(S_REV "ab") → "ba"            (S_REV "12345") → "54321"
```

### CONCAT — Join strings together
```
(CONCAT "hello" " " "world") → "hello world"
(CONCAT "a" "b") → "ab"        (CONCAT "" "x") → "x"
(CONCAT "cat" "s") → "cats"    (CONCAT "1" "2" "3") → "123"
```
**Variadic.** Any number of strings joined end to end.

### S_CHAR — Number to character
```
(S_CHAR 65) → "A"         (S_CHAR 97) → "a"
(S_CHAR 48) → "0"         (S_CHAR 32) → " "
(S_CHAR 90) → "Z"         (S_CHAR 122) → "z"
```
**The number IS the character's address in the base layer.**

### S_CODE — Character to number
```
(S_CODE "A") → 65         (S_CODE "a") → 97
(S_CODE "0") → 48         (S_CODE " ") → 32
(S_CODE "Z") → 90         (S_CODE "z") → 122
```
**Inverse of S_CHAR.** S_CHAR and S_CODE undo each other.

### S_CONTAINS — Is this inside that?
```
(S_CONTAINS "hello" "ell") → true     (S_CONTAINS "hello" "xyz") → false
(S_CONTAINS "hello" "hello") → true   (S_CONTAINS "hello" "") → true
(S_CONTAINS "cat" "at") → true        (S_CONTAINS "cat" "dog") → false
```

---

## Level 8: Type Operations

### IS_NUM — Is this a number?
```
(IS_NUM 5) → true         (IS_NUM "hello") → false
(IS_NUM 0) → true         (IS_NUM true) → false
(IS_NUM -3) → true        (IS_NUM "") → false
```

### IS_STR — Is this a string?
```
(IS_STR "hello") → true   (IS_STR 5) → false
(IS_STR "") → true        (IS_STR true) → false
(IS_STR "a") → true       (IS_STR 0) → false
```

### IS_BOOL — Is this a boolean?
```
(IS_BOOL true) → true     (IS_BOOL 5) → false
(IS_BOOL false) → true    (IS_BOOL "hello") → false
```

### TYPE_OF — What kind of thing is this?
```
(TYPE_OF 5) → "number"         (TYPE_OF "hello") → "string"
(TYPE_OF true) → "boolean"     (TYPE_OF null) → "null"
(TYPE_OF false) → "boolean"    (TYPE_OF 0) → "number"
```

### TO_NUM — Convert to number
```
(TO_NUM "5") → 5          (TO_NUM "0") → 0
(TO_NUM true) → 1         (TO_NUM false) → 0
(TO_NUM "3.14") → 3.14    (TO_NUM "") → 0
```

### TO_STR — Convert to string
```
(TO_STR 5) → "5"          (TO_STR 0) → "0"
(TO_STR true) → "true"    (TO_STR false) → "false"
(TO_STR 3.14) → "3.14"    (TO_STR -1) → "-1"
```

---

## Level 9: Control

### IF — Choose based on condition
```
(IF true 1 2) → 1              (IF false 1 2) → 2
(IF true "yes" "no") → "yes"   (IF false "yes" "no") → "no"
(IF (EQ 1 1) 10 20) → 10       (IF (GT 5 3) "big" "small") → "big"
(IF (LT 5 3) "big" "small") → "small"
```
**Three inputs:** condition, then-value, else-value.
**Uses Level 1 tools (EQ, GT, LT) inside the condition.** This is why IF comes after comparison.

---

## Level 10: Bitwise (Advanced)

### BIT_AND, BIT_OR, BIT_XOR
```
(BIT_AND 12 10) → 8       (BIT_OR 12 10) → 14
(BIT_XOR 12 10) → 6       (BIT_AND 15 7) → 7
(BIT_OR 0 5) → 5          (BIT_XOR 5 5) → 0
```
**Operates on the binary representation of numbers.** Advanced — requires understanding numbers as bit patterns.

---

## How the System Uses This

1. **Verify:** Run every example. Does (ADD 1 2) actually give 3? Confirm.
2. **Discover:** Look at all the confirmed examples. What's the pattern?
3. **Predict:** Generate a NEW input. Predict the output. Run it. Check.
4. **Streak:** 10 novel correct predictions in a row = TRUSTED.
5. **Use:** Now this tool is available for verifying the NEXT level's tools.

Each level unlocks the next. EQ lets you check ADD. ADD lets you check MUL. The system bootstraps its own verification capability.

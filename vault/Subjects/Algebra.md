---
source: alcumus
type: subject
subject_id: 2
level: 9
xp: 13266
correct: 176
incorrect: 15
gave_up: 34
accuracy: 78%
updated: 2026-08-17T22:24:14
tags: [alcumus, subject, algebra]
---

# Algebra

Subject in [[Alcumus]].

## Explanation

### L1 · Intuition — the picture in your head

Arithmetic asks *what is the answer*. Algebra asks *what must be true*.

That shift is the whole subject. An equation is not a question to compute — it's
a **constraint**, a filter on possibilities. $3x + 1 = 10$ doesn't mean "do
something to 10"; it names the set of all $x$ satisfying a condition, and that
set happens to have one element.

Solving is **narrowing**, not calculating. You start with "$x$ is some number"
and apply operations that preserve the solution set until only the answer is
left standing. Every legal move is legal for exactly one reason: it doesn't
change which values satisfy the statement.

This explains the rule everyone learns and nobody is told the reason for — *do
the same thing to both sides*. An equation asserts two expressions are the same
object. Applying a function to the same object twice can't produce different
results, so the truth survives. **The rule isn't a ritual; it's a consequence of
what "equals" means.**

It also explains where solutions go wrong. Squaring both sides is not reversible:
$x = 3$ and $x = -3$ both square to $9$, so squaring *widens* the solution set
and can admit roots that were never there. Dividing by $x$ *narrows* it, silently
discarding $x = 0$. **Extraneous and lost roots aren't mistakes in arithmetic —
they're operations that changed the question.**

### L2 · Mechanics — the strands

Alcumus's Algebra tree is large, but it's a handful of ideas revisited at
increasing depth:

| Strand | The core question |
| --- | --- |
| Expressions & identities | rewriting without changing value |
| Linear equations | one constraint, one unknown |
| Systems & lines | several constraints at once — see [[Graphing Multiple Lines]] |
| Quadratics | when the unknown multiplies itself |
| Polynomials | what roots and coefficients say about each other |
| Inequalities | constraints that give ranges, not points |
| Functions | the machine view: input, output, inverse |
| Exponentials & logs | when the unknown sits in the exponent |
| Sequences & series | infinitely many terms, finitely many words |

The through-line: **each strand adds one way for the unknown to appear**, and
each needs one new technique to isolate it.

### L3 · Fluency — seeing it fast

- **Recognise form before computing.** A quadratic in disguise ($x^4 - 5x^2 + 4$,
  or $2^{2t} - 5 \cdot 2^t + 4$) is still a quadratic. Substitution reveals it.
- **Factoring beats the formula** when factors are small. The quadratic formula
  always works and is always slower.
- **Symmetry is a shortcut.** Symmetric systems usually want $s = x+y$,
  $p = xy$ rather than brute substitution.
- **Vieta over root-finding.** If a question asks about the *sum* or *product*
  of roots, you almost never need the roots — see L4.
- **Sanity-check at the end**: substitute back. Squaring and cross-multiplying
  both invite extraneous roots, and one substitution catches them.

### L4 · Competition — AMC / AIME level

**Vieta's formulas.** For $ax^2 + bx + c = 0$: $\;r_1 + r_2 = -\frac{b}{a}$,
$\;r_1 r_2 = \frac{c}{a}$. Generalises to every degree, and turns most
"find the sum of the roots" problems into one line.

**The classical inequalities.** AM–GM is the workhorse:

$$\frac{x_1 + \cdots + x_n}{n} \ge \sqrt[n]{x_1 \cdots x_n}$$

with equality exactly when all terms are equal — the equality case is usually
where the answer hides. Cauchy–Schwarz handles sums of products.

**Telescoping and partial fractions.** A sum that looks intractable often
collapses once each term is split into a difference.

**Substitution to force symmetry.** Shifting $x \to x + k$ to kill a linear term,
or $x \to 1/x$ to exploit reciprocal structure, is standard AIME practice.

### L5 · Deeper — olympiad and the structure underneath

**Algebra is the study of structure-preserving operations.** School algebra works
in one structure — the field $\mathbb{R}$ — where addition and multiplication are
associative, commutative, distributive, and invertible (except division by zero).
Every manipulation is licensed by one of those axioms. Change the structure and
the rules change with it: matrices lose commutativity, modular arithmetic gains
zero divisors.

**A polynomial is more than a function.** Over $\mathbb{R}$, $x^2 + 1$ has no
roots; over $\mathbb{C}$ it has two. The Fundamental Theorem of Algebra says
$\mathbb{C}$ is *algebraically closed* — every degree-$n$ polynomial has exactly
$n$ roots with multiplicity. Factoring is then not a trick but a guarantee, and
Vieta's formulas are just the expansion of $a\prod(x - r_i)$.

**Solvability has a limit, and it's a theorem.** Quadratic, cubic, and quartic
equations have radical formulas; the quintic does not. Galois theory explains
why by attaching a group to each polynomial — the symmetries of its roots — and
showing radical solvability corresponds to that group being *solvable*. **Algebra
answers a question about itself: which equations can be solved by the operations
algebra provides.**

**Functional equations** are the olympiad face of the subject. Instead of solving
for a number you solve for a *function*, and the tools are substitution,
injectivity/surjectivity arguments, and fixed points rather than manipulation.

### Where marks get lost

- **Squaring without checking.** It adds roots. Always substitute back.
- **Dividing by an expression that might be zero** — you lose a solution
  silently. Factor instead and consider both cases.
- **Sign errors distributing a negative** across a bracket.
- **Losing the domain** in log and radical problems: the answer must be in it.
- **Ignoring the equality case** in an inequality — it's usually the question.
- **Answering the wrong thing**: the problem asked for $x^2$, you found $x$.

## Notes


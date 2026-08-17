---
source: alcumus
type: topic
topic_id: 85
subject: Algebra
status: ready
progress: 53.1
correct: 7
incorrect: 2
gave_up: 2
accuracy: 64%
updated: 2026-08-17T22:24:14
tags: [alcumus, topic, graphing-multiple-lines]
---

# Graphing Multiple Lines

Topic in [[Algebra]] · [[Alcumus]]

## Explanation

### L1 · Intuition — the picture in your head

A line is **a direction plus a position**. Nothing else. Every question in this
topic is really asking about one of those two things.

The slope *is* the direction. Saying $m = \frac{3}{7}$ means "walk 7 right, rise
3" — it's a travel instruction, not a number you memorise a formula for.

```
        y
        │        ╱  m = 3/7
        │      ╱ ┊
        │    ╱   ┊ rise 3
        │  ╱ ┄┄┄┄┘
        │╱   run 7
    ────┼──────────────── x
        │
```

Once you see slope as direction, two facts stop being rules and become obvious:

**Parallel means same direction.** Same slope, different position. That's the
whole idea — they point the same way, so they never converge.

**Perpendicular means turn 90°.** Here's the part worth actually seeing. Encode
direction as a vector: slope $m$ is the vector $(1, m)$ — one right, $m$ up.
Rotating any vector 90° counter-clockwise sends

$$(x, y) \longmapsto (-y, x)$$

so our direction $(1, m)$ becomes $(-m, 1)$. The slope of *that* vector is
rise over run:

$$m_{\perp} = \frac{1}{-m} = -\frac{1}{m}$$

**The negative reciprocal isn't a rule — it's what a quarter turn does to a
slope.** Flip and negate falls straight out of the rotation.

The same trick demystifies standard form. For $Ax + By = C$, the vector $(A, B)$
is the **normal** — it points perpendicular to the line. So the line's own
direction is $(A,B)$ rotated 90°, which is $(-B, A)$, giving

$$m = \frac{A}{-B} = -\frac{A}{B}$$

That minus sign everyone drops is just the rotation showing up again.

### L2 · Mechanics — how to actually do it

| Form | Looks like | Good for |
| --- | --- | --- |
| Slope-intercept | $y = mx + b$ | reading slope $m$ and $y$-intercept $b$ |
| Standard | $Ax + By = C$ | how Alcumus usually *gives* you a line |
| Point-slope | $y - y_1 = m(x - x_1)$ | building a line through a known point |

The relationships:

$$\text{parallel: } m_1 = m_2 \qquad\qquad \text{perpendicular: } m_1 m_2 = -1$$

Two parallel lines with different intercepts have **no solution**; if the
intercepts match too, the lines are identical and there are **infinitely many**.
Alcumus tests that distinction often.

**The recipe.** Most problems here are the same four steps:

1. **Find the slope of the given line** — convert to $y = mx + b$, or read $-A/B$.
2. **Transform it** — keep it (parallel) or negative-reciprocal it (perpendicular).
3. **Anchor to the point** with point-slope: $y - y_1 = m(x - x_1)$.
4. **Answer what was asked** — often an intercept, not the equation.

**Worked example.**

> A line parallel to $2x + 5y = 20$ passes through $(5, 3)$. Where does it cross
> the $y$-axis?

*1 — slope.* With $A = 2$, $B = 5$: $\;m = -\frac{A}{B} = -\frac{2}{5}$.

*2 — transform.* Parallel, so the slope is unchanged: $m = -\frac{2}{5}$.

*3 — anchor to $(5,3)$.*

$$y - 3 = -\frac{2}{5}(x - 5)$$
$$y = 3 - \frac{2}{5}x + 2 = 5 - \frac{2}{5}x$$

*4 — answer.* The $y$-axis is $x = 0$, so $y = 5$: the crossing is $(0, 5)$.

*Check:* at $x = 5$, $y = 5 - 2 = 3$. ✓ The point lies on the line.

### L3 · Fluency — seeing it fast

**Never convert to slope-intercept just to go parallel.** Every line parallel to
$Ax + By = C$ has the form

$$Ax + By = C'$$

because parallel means *same normal vector*. So substitute the point to get $C'$
in one line. Redoing the example above: $2(5) + 5(3) = 25$, hence $2x + 5y = 25$;
set $x = 0$ and $5y = 25$ gives $y = 5$. **Three steps collapse into one.**

The perpendicular version: swap the coefficients and negate one.

$$Ax + By = C \quad\longrightarrow\quad Bx - Ay = C'$$

Again, plug in the point for $C'$. No fractions, no reciprocals, no sign errors —
which matters because fractional slopes are where arithmetic goes to die.

**Recognising the shape in one read.** "Parallel/perpendicular … through the
point … find the intercept" is a single problem with three variations. Spot it
and you know the whole path before you write anything.

**Sanity checks that cost seconds:**

- Does the sign of your slope match the picture? $2x + 5y = 20$ falls left to
  right, so $m$ must be negative.
- Substitute the given point back into your final equation. It must satisfy it.
- $y$-intercept means $x = 0$; $x$-intercept means $y = 0$. Misreading this is
  the single most common way to lose a correct piece of work.

<details>
<summary><b>L4 · Competition — AMC / AIME level</b> — click to expand</summary>

**Distance between parallel lines.** For $Ax + By = C_1$ and $Ax + By = C_2$:

$$d = \frac{|C_1 - C_2|}{\sqrt{A^2 + B^2}}$$

Note it only works when the coefficients match — normalise first.

**Angle between two lines.**

$$\tan\theta = \left|\frac{m_1 - m_2}{1 + m_1 m_2}\right|$$

The perpendicular rule is just the case where the denominator vanishes: $\theta$
hits $90°$ exactly when $1 + m_1m_2 = 0$.

**The pencil trick.** If $L_1 = 0$ and $L_2 = 0$ meet at a point, then

$$L_1 + \lambda L_2 = 0$$

is a line through that intersection **for every** $\lambda$ — and you never had
to compute the intersection. When a problem says "the line through the
intersection of … and …", this saves a whole system solve. Choose $\lambda$ to
satisfy the remaining condition.

**Concurrency.** Three lines $A_ix + B_iy = C_i$ meet at one point iff

$$\begin{vmatrix} A_1 & B_1 & C_1 \\ A_2 & B_2 & C_2 \\ A_3 & B_3 & C_3 \end{vmatrix} = 0$$

**Lattice-point traps.** Contest problems love asking for integer solutions on a
line. $Ax + By = C$ has integer points iff $\gcd(A,B) \mid C$ — that's Bézout,
and it turns a geometry question into number theory.

</details>

<details>
<summary><b>L5 · Deeper — olympiad and the structure underneath</b> — click to expand</summary>

**A line is a level set.** $Ax + By = C$ says: the linear functional
$f(x,y) = Ax + By$ takes the value $C$. Varying $C$ sweeps out parallel lines —
so *parallel lines are level sets of the same functional*. Parallelism isn't a
property of two lines; it's them sharing a functional.

**Determinants decide everything.** Two lines as a system have matrix
$\begin{pmatrix} A_1 & B_1 \\ A_2 & B_2\end{pmatrix}$. Its determinant
$A_1B_2 - A_2B_1$ is zero exactly when the normals are proportional — i.e. when
the lines are parallel or identical. **Non-zero determinant ⟺ exactly one
intersection**, and Cramer's rule hands you the point. The entire
parallel/intersecting/identical trichotomy is one number.

**Projective geometry: parallel lines do meet.** Move to homogeneous coordinates
$(x : y : z)$, where the affine point $(x,y)$ is $(x : y : 1)$ and $z = 0$ gives
the *line at infinity*. A line becomes $Ax + By + Cz = 0$. Now solve two parallel
lines: the normals are proportional, and the solution comes out with $z = 0$ —
a point at infinity, one for each direction.

The payoff: **the trichotomy disappears.** Any two distinct lines meet in exactly
one point, always. Parallel lines are simply those meeting on the line at
infinity, and the pencil $\lambda L_1 + \mu L_2$ from L4 is the family of lines
through that meeting point — whether it's finite or infinite. "Parallel" and
"intersecting" stop being different cases.

**Duality.** In the projective plane, points and lines are interchangeable:
$(a:b:c)$ can name either. Every theorem has a dual obtained by swapping the
words — three points are collinear exactly when three lines are concurrent, and
both conditions are the same determinant. This is why the concurrency formula in
L4 looks identical to the collinearity test.

**Where L1's intuition breaks.** Slope-as-direction quietly assumes a vertical
line is special: $x = c$ has no slope, and $m_1m_2 = -1$ fails for it. That's an
artifact of the coordinate choice, not the geometry. Direction vectors and
normal vectors have no such gap — $(0,1)$ is a perfectly ordinary vector. Whenever
a formula here needs an "unless the line is vertical" caveat, that's a sign you're
using slopes where vectors would be cleaner.

</details>

### Where marks get lost

- **Dropping the minus** in $m = -A/B$. Check against the picture: does the line
  fall or rise?
- **Negating without flipping** — the perpendicular of $\frac{3}{7}$ is
  $-\frac{7}{3}$, not $-\frac{3}{7}$.
- **Stopping at the equation** when the question asked for an intercept or a
  coordinate.
- **Forgetting the $y$-axis is $x = 0$** (and the $x$-axis is $y = 0$).
- **Vertical lines**, silently. If a slope is undefined, the slope formulas
  don't apply — handle it by inspection.
- **Decimalising fractional slopes.** $-\frac{2}{5}$ stays a fraction; $-0.4$
  invites rounding drift.
- **Assuming parallel means no solution** without checking the intercepts — they
  might be the same line.

## Notes


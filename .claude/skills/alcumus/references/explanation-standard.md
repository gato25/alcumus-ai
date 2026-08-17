# The explanation standard

How to write `## Explanation` in a subject or topic note.

The target is **3Blue1Brown for the intuition, AoPS for the technique**. A reader
should come away able to *see* why the thing is true, and also able to use it
under time pressure.

## The five levels

Every explanation is written in ascending levels, so the same note serves a
beginner and someone prepping for an olympiad. Use these exact headings:

```markdown
### L1 · Intuition — the picture in your head
### L2 · Mechanics — how to actually do it
### L3 · Fluency — seeing it fast
### L4 · Competition — AMC / AIME level
### L5 · Deeper — olympiad and the structure underneath
```

Skip a level only when it genuinely has nothing to say, and say so in one line
rather than padding it.

### L1 · Intuition

The 3Blue1Brown level. No procedure yet — the mental image.

- Answer "what is this *really*?" before "how do I compute it?"
- Reach for geometry, motion, or a physical analogy
- **Derive the formula from the picture** rather than stating it. The reader
  should feel the rule was inevitable, not handed down
- Best possible outcome: a rule they had memorised becomes obvious

### L2 · Mechanics

The school level. The standard method, done properly.

- The forms/formulas, stated cleanly as `$…$` or `$$…$$`
- A numbered recipe for the standard problem shape
- **One fully worked example**, every line shown, with a check at the end
- Never use the live problem as the example — that hands over the answer

### L3 · Fluency

The Alcumus level: same maths, less work.

- Shortcuts that skip the long method, and *why* they're valid
- How to recognise the problem shape in one read
- What to do in your head vs. on paper
- Sanity checks that catch errors before they cost marks

### L4 · Competition

AMC/AIME level. Where the topic actually shows up in contests.

- The non-obvious applications and standard contest tricks
- Formulas worth knowing that school never covers
- Traps specific to multiple-choice/short-answer formats

### L5 · Deeper

Olympiad and beyond. Why the structure is what it is.

- The general statement the school rule is a special case of
- Connections to other fields — linear algebra, projective geometry, analysis
- Where the intuition from L1 breaks down, and what replaces it
- This is allowed to be hard. It is the ceiling, not the entry point

## After the levels

Close with:

```markdown
### Where marks get lost
```

A blunt list of the actual errors people make in this topic — sign slips,
misread questions, forgotten edge cases. Concrete, not generic advice.

## Style

- **LaTeX everywhere**: `$…$` inline, `$$…$$` for anything you'd want to stare
  at. Obsidian renders both.
- **Tables** for form/comparison material.
- **ASCII diagrams** in code fences where a picture beats a paragraph. Keep them
  small and honest.
- Write prose, not bullet soup. A bulleted list of formulas explains nothing.
- Bold the load-bearing sentence in a section, not scattered keywords.
- Cross-link with `[[Topic]]` when a neighbouring topic is genuinely needed —
  those links are what make the graph view worth opening.

## Length

A topic note earns 100–200 lines. A subject note is a **map**: what the field is
about, its main strands, how they connect, and the ladder from school to
olympiad — it should link out to topics rather than duplicate them.

Stop when it's genuinely useful. Padding to hit a length is worse than a short,
dense note.

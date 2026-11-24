# Notes for agents working on this repo

This repo ships instructions a model follows. A wrong sentence here is a wrong
number in someone's report, so the bar is different from a normal library.

## What must stay true

- `SKILL.md` names **no data vendor**. A capability, a free route, and a paid
  route if one exists. If you add a tool name, add it as an example, never as a
  requirement.
- Every dollar figure in the guidance carries a range and says "estimate".
  Every count says "counted" or "pulled N of M".
- Money and counts in the docs match `scripts/rab.py` exactly. Change the code
  and the reference file in the same commit. `tests/test_rab.py` fails if they
  drift in the parts the script owns.
- The verdict gate is the product. Do not soften it: volume alone never decides,
  and "too early to call" always carries the date it becomes final.
- Blank is not zero. A week you didn't pull is "not pulled".

## Changing a rule

1. Make the change in `scripts/rab.py` first, with a test that fails without it.
2. Update `references/estimates.md` (or whichever reference owns it) in the same
   commit, in the same words.
3. If the change would alter an existing report's numbers, say so in the commit
   message. A silent rate change is how a teardown becomes wrong.

## The script

Standard library only, Python 3.9+, no network, no clock except `today` where it
is explicit. Deterministic output: same inputs, same CSV. `--json` on every
command. Exit 2 for bad input, 1 for a failed check.

## SKILL.md style

- Second person, present tense, short sentences. No marketing voice.
- Tables for anything a reader will scan twice.
- A reference file is for the step it belongs to. Do not turn `SKILL.md` into a
  reading list.
- Keep frontmatter `name` equal to the folder name; the skills CLI matches them.

## Trying it

```bash
python3 tests/test_rab.py
python3 skills/reverse-any-brand/scripts/rab.py init --dir /tmp/try
python3 skills/reverse-any-brand/scripts/rab.py window "black friday" --year 2026
```

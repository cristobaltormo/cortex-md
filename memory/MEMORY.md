# Memory index

This index is short on purpose: it is loaded whole in every session. Detail lives in the area
indexes (opened only when the topic comes up) and in each note. Hard rules live in your
`CLAUDE.md`.

## Always read when relevant

- [Working preferences](preferences-communication.md) - how the user wants answers and code
- [Deployments need approval](feedback-deploys-need-approval.md) - nothing goes to production unasked

## Area indexes

- [How to work with the user](index-working-style.md) - preferences, review habits, conventions
- [Projects](index-projects.md) - what each project is and which note to read
- [Infrastructure](index-infrastructure.md) - decisions and quirks of the machines

## Search

`grep -ril "word" memory/` finds any note; the per-message hook already suggests the likeliest.

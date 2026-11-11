# Contributing

Thanks for taking the time. This project is small on purpose, so the bar is simple: a change should
make the brain more trustworthy or easier to adopt, and it should keep the engine dependency-free.

## Ground rules

- Python standard library only. Shell scripts target bash on Linux.
- No comments in code. The reasoning goes in the README, the skills or the commit message.
- No emojis anywhere.
- Every behavior change needs a test in `tests/test_engine.py`.

## Setup

```bash
git clone https://github.com/cristobaltormo/cortex-md
cd cortex-md
make check
```

`make check` runs ShellCheck, byte-compiles the Python, runs the tests and runs the validator on the
example brain. ShellCheck is optional locally and always runs in CI.

## Proposing a change

1. Open an issue first for anything beyond a small fix, so the direction can be agreed.
2. Branch from `main`, keep the change focused, and write the commit message in English, imperative
   mood, explaining why more than what.
3. Open a pull request. CI must be green.

## What fits and what does not

Fits: new inventory collectors, better validator checks, safer curator behavior, documentation,
fixes for any platform quirk.

Does not fit: a database, an embedding index or a service that must run alongside. The point is
plain files and `grep`. If retrieval ever needs more, the answer is an index note first.

## Reporting bugs

Use the bug report form and include the output of `bin/health.py` and your OS. For security issues,
see [SECURITY.md](SECURITY.md).

#!/usr/bin/env bash
set -uo pipefail
BRAIN="${BRAIN_DIR:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"
. "$BRAIN/bin/load-env.sh"
MODEL="${CURATOR_MODEL:-sonnet}"
CLAUDE_BIN="${CLAUDE_BIN:-claude}"
LOG="$BRAIN/state/curator.log"
mkdir -p "$BRAIN/state"

exec 9>"$BRAIN/state/curator.lock"
flock -n 9 || { echo "[$(date '+%F %T')] another curator is already running" >> "$LOG"; exit 0; }

if [ -f "$LOG" ] && [ "$(stat -c %s "$LOG")" -gt 1000000 ]; then
  tail -c 300000 "$LOG" > "$LOG.tmp" && mv "$LOG.tmp" "$LOG"
fi

TRANSCRIPTS=$(python3 "$BRAIN/bin/transcripts.py" --days 1 2>/dev/null)
NEW=$(printf '%s' "$TRANSCRIPTS" | grep -c .)
PROBLEMS=$("$BRAIN/bin/health.py" --brief 2>/dev/null | wc -l)
if [ "$NEW" -eq 0 ] && [ "$PROBLEMS" -eq 0 ]; then
  echo "[$(date '+%F %T')] no new transcripts and the brain is healthy, not running" >> "$LOG"
  exit 0
fi

PROMPT=$(cat <<EOT
You are the curator of this brain (the directory $BRAIN). First read the skill
"memory-keeping" ($BRAIN/skills/memory-keeping/SKILL.md) and follow its rules to the letter.

Tonight's work, in this order:

1. DISTILL. These are the conversation transcripts modified in the last 24 hours, one per line as
   "agent<TAB>path" (Claude Code, Antigravity CLI and Codex CLI are all read):
$TRANSCRIPTS
   Use Grep to find the relevant lines and Read with offset to read them; transcripts can be huge.
   Formats: Claude Code lines have "type":"user" or "assistant" with message.content; Antigravity
   lines have "type":"USER_INPUT" (the request is inside <USER_REQUEST> tags) and "PLANNER_RESPONSE";
   Codex rollout lines carry a payload with a role. Ignore system and hook messages.
   Look ONLY for: decisions with their reason, preferences the user expressed, procedures that
   were hard to discover, and devices or services that behave unexpectedly. Zero or one note is
   the normal outcome. Do not invent material to justify the run; if there is nothing worth
   keeping, say so and move on.

2. REACT TO MACHINE CHANGES. Read $BRAIN/inventory/CHANGES.md, entries of the last 2 days. For
   each change, grep the notes in $BRAIN/memory/ that talk about it and update them:
   - A container or machine that DISAPPEARED: mark the notes that describe it status: historical,
     say in the note when it stopped existing, and remove it from PENDING.md. Do not delete them.
   - A NEW one with its own weight: record what it is for if the conversations say so; if not,
     do not invent it, add a question to PENDING.md.
   - Changed resources, addresses or ports: fix any note that assumes the old values.

3. RE-VERIFY. For each note whose verified date is older than 30 days and that can be checked
   from this host, check it for real. If it is still true, bump the date. If not, correct the
   note and mark the old content as historical inside the same file.

4. CONSOLIDATE. Fix every defect in the list below: orphan notes, broken [[links]], notes
   without a verified date, notes that are too large (split by topic, not in half), and any
   credential that slipped in. When finished, confirm it is clean with:
       python3 $BRAIN/bin/health.py

5. PENDING. Update $BRAIN/PENDING.md: remove what is closed (it stays in git), add what is half
   done or waiting for a decision. It is loaded at the start of every session, so keep it short
   and true.

6. SAVE. git add -A and git commit with a message saying what you learned or corrected tonight.
   If there is nothing to commit, do not force an empty commit.

Do not touch $BRAIN/inventory/ (a script generates it). Never write credentials in any note.
When in doubt between adding and not adding, do not add.
EOT
)

if [ "$PROBLEMS" -gt 0 ]; then
  PROMPT="$PROMPT

DEFECTS FOUND BY THE VALIDATOR RIGHT NOW ($PROBLEMS):
$("$BRAIN/bin/health.py" --brief 2>/dev/null | sed 's/^/  - /')"
fi

echo "[$(date '+%F %T')] starting curator ($NEW new transcripts, $PROBLEMS things to fix)" >> "$LOG"

cd "$BRAIN" || exit 1
OUT=$(mktemp)
timeout 900 "$CLAUDE_BIN" -p "$PROMPT" \
  --model "$MODEL" \
  --allowedTools "Read,Grep,Glob,Skill,Write($BRAIN/memory/**),Edit($BRAIN/memory/**),Edit($BRAIN/PENDING.md),Write($BRAIN/skills/**),Edit($BRAIN/skills/**),Bash(git add:*),Bash(git commit:*),Bash(git status:*),Bash(git diff:*),Bash(git log:*),Bash(ls:*),Bash(grep:*),Bash(python3 $BRAIN/bin/health.py:*)" \
  > "$OUT" 2>&1
CODE=$?
cat "$OUT" >> "$LOG"

FAILS_FILE="$BRAIN/state/consecutive-failures"
FAIL_DAY_FILE="$BRAIN/state/last-failure-day"
RETRY_AT="$BRAIN/state/retry-at"
TODAY=$(date '+%F')
LIMIT_RE="session limit|usage limit|rate.?limit|quota"
LIMITED=0
if [ "$CODE" -ne 0 ]; then
  grep -qiE "$LIMIT_RE" "$OUT" && LIMITED=1
elif [ "$(wc -l < "$OUT")" -le 3 ] && grep -qiE "$LIMIT_RE" "$OUT"; then
  LIMITED=1
fi
if [ "$CODE" -ne 0 ] || [ "$LIMITED" -eq 1 ]; then
  RESET=$(grep -oiE 'resets [0-9]{1,2}:[0-9]{2}\s*(am|pm)' "$OUT" | head -1 | sed -E 's/^[Rr]esets //')
  BASE=""
  [ -n "$RESET" ] && BASE=$(date -d "$RESET" +%s 2>/dev/null)
  NOW=$(date +%s)
  if [ -n "$BASE" ]; then
    [ "$BASE" -le "$NOW" ] && BASE=$(date -d "tomorrow $RESET" +%s)
    RETRY=$((BASE + 300))
  else
    RETRY=$((NOW + 21600))
  fi
  echo "$RETRY" > "$RETRY_AT"
  echo "[$(date '+%F %T')] curator FAILED (exit $CODE), retry scheduled for $(date -d "@$RETRY" '+%F %T')" >> "$LOG"
  if [ ! -f "$FAIL_DAY_FILE" ] || [ "$(cat "$FAIL_DAY_FILE")" != "$TODAY" ]; then
    FAILS=$(( $(cat "$FAILS_FILE" 2>/dev/null || echo 0) + 1 ))
    echo "$FAILS" > "$FAILS_FILE"
    echo "$TODAY" > "$FAIL_DAY_FILE"
  else
    FAILS=$(cat "$FAILS_FILE" 2>/dev/null || echo 1)
  fi
  if [ "$FAILS" -ge 2 ]; then
    "$BRAIN/bin/notify.sh" "Brain curator" "It has failed $FAILS nights in a row. Check state/curator.log."
  fi
else
  echo "[$(date '+%F %T')] curator finished (exit $CODE)" >> "$LOG"
  rm -f "$RETRY_AT" "$FAILS_FILE" "$FAIL_DAY_FILE"
fi
rm -f "$OUT"

if git remote get-url origin >/dev/null 2>&1; then
  timeout 30 git push --quiet -u origin HEAD 2>/dev/null || true
fi

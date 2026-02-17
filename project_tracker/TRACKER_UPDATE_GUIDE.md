# Project Tracker - Update Guide for Claude

## Purpose
This guide explains how Claude should update `project-state.json` after each work session with Santiago.

---

## When to Update

Update the tracker whenever:
1. A task changes status (not_started → in_progress → done)
2. Subtasks are completed
3. Santiago shares code or mentions progress on a task
4. A new decision is made that affects the roadmap
5. Tasks are blocked or unblocked

---

## How Claude Estimates Progress

### For Tasks WITH Subtasks (Explicit Tracking)
Progress = (completed_subtasks / total_subtasks) × 100

Example:
```json
{
  "id": "task-007",
  "progress": 60,  // 3 out of 5 subtasks done
  "subtasks": [
    {"id": "subtask-007-1", "completed": true},
    {"id": "subtask-007-2", "completed": true},
    {"id": "subtask-007-3", "completed": true},
    {"id": "subtask-007-4", "completed": false},
    {"id": "subtask-007-5", "completed": false}
  ]
}
```

### For Tasks WITHOUT Subtasks (Conversational Inference)

Claude should analyze the conversation and estimate:

| User Signal | Progress Estimate |
|-------------|------------------|
| "I'm starting X" | 25% |
| "I created the file/setup" | 30-40% |
| "Here's the code for X" (shares code) | 50-60% |
| "X works but needs Y" | 75% |
| "X is done" or "Finished X" | 100% |
| "X is broken" or "stuck on X" | Keep previous % |

Example conversation flow:
```
User: "I started working on the BaseCallbackHandler"
→ Claude updates task-007: progress: 25, status: "in_progress"

User: "Here's my interceptor.py file [shares code]"
→ Claude updates task-007: progress: 50

User: "The callback works for on_chain_start!"
→ Claude updates subtask-007-2: completed: true
→ Recalculates: progress: 60 (3/5 subtasks)
```

---

## Status Transitions

Valid status values and their transitions:

```
not_started → in_progress → done
              ↓
            blocked → in_progress
```

**Status Rules:**
- `not_started`: Task hasn't been touched
- `in_progress`: User is actively working on it or mentioned starting it
- `blocked`: Dependencies not met OR user explicitly says "I'm stuck because..."
- `done`: User confirms completion OR all subtasks completed
- `backlog`: Future work, not part of active sprint

---

## Update Process (Step-by-Step)

### Step 1: Identify What Changed
After each conversation, Claude should mentally note:
- Which tasks were discussed?
- Did Santiago share code?
- Did Santiago say "done", "started", "blocked"?
- Were any decisions made that affect the roadmap?

### Step 2: Update task fields

For each affected task, update:

```json
{
  "id": "task-XXX",
  "status": "in_progress",  // Update if changed
  "progress": 50,           // Recalculate based on subtasks OR inference
  "subtasks": [             // Mark completed ones
    {"id": "...", "completed": true}
  ],
  "notes": "Updated based on session 2: user implemented basic callback"
}
```

### Step 3: Update phase progress

Recalculate phase progress:
```
phase.progress = average(all_task_progress_in_that_phase)
```

### Step 4: Add session history entry

```json
{
  "session_history": [
    {
      "date": "2026-02-16",
      "session_number": 2,
      "summary": "Started Phase 1. Set up project structure and created test agent.",
      "decisions": [
        "Used pytest instead of unittest",
        "Decided to start with sync-only support"
      ],
      "tasks_updated": ["task-001", "task-002"],
      "next_session_goals": [
        "Implement stream-based capture (task-003)",
        "Build basic terminal reporter (task-004)"
      ]
    }
  ]
}
```

### Step 5: Update metadata

```json
{
  "metadata": {
    "last_updated": "2026-02-16T14:30:00Z",
    "version": "1.1"
  }
}
```

---

## Example Update Scenario

**User says:**
> "Hey Claude, I just finished setting up the repo. I've got the pyproject.toml working and can do `pip install -e .` successfully. Also created the basic package structure with `__init__.py`."

**Claude should:**

1. **Identify affected task:** task-001 (Project Setup)

2. **Update subtasks:**
```json
{
  "id": "task-001",
  "status": "in_progress",
  "progress": 75,  // 3 out of 4 subtasks done
  "subtasks": [
    {"id": "subtask-001-1", "completed": false},  // README not done yet
    {"id": "subtask-001-2", "completed": true},   // pyproject.toml ✅
    {"id": "subtask-001-3", "completed": true},   // package structure ✅
    {"id": "subtask-001-4", "completed": true}    // pip install works ✅
  ]
}
```

3. **Update phase-1 progress:**
```json
{
  "id": "phase-1",
  "status": "in_progress",
  "progress": 12  // Only 1 task out of 6 has meaningful progress
}
```

4. **Add session entry:**
```json
{
  "date": "2026-02-16",
  "session_number": 2,
  "summary": "Completed project setup. Package is installable.",
  "tasks_updated": ["task-001"],
  "next_session_goals": ["Finish README", "Start building test agent"]
}
```

---

## What NOT to Do

❌ **Don't update progress without evidence**
- If user just asks a question about X, don't mark X as in_progress

❌ **Don't mark tasks as done prematurely**
- Wait for user confirmation or all subtasks completed

❌ **Don't infer blocking without user saying so**
- Only set status="blocked" if user explicitly mentions being stuck

❌ **Don't edit past session history**
- Only append new sessions, never modify old ones

---

## Handling Ambiguity

If unsure about progress, Claude should:

1. **Ask the user directly:**
   > "Before I update the tracker, can you confirm: did you complete the BaseCallbackHandler or is it still in progress?"

2. **Use conservative estimates:**
   - If doubt between 50% and 75%, choose 50%
   - Better to underestimate than overestimate

3. **Note uncertainty in task.notes:**
   ```json
   {
     "notes": "User mentioned working on this but didn't share code. Estimated 25% conservatively."
   }
   ```

---

## Regenerating the HTML

After updating `project-state.json`, Claude does NOT need to regenerate the HTML file. The HTML reads the JSON dynamically via JavaScript, so changes are reflected immediately on page refresh.

**Only regenerate HTML if:**
- Adding new UI features
- Fixing bugs in the visualization
- User requests a design change

---

## Quick Reference: JSON Schema

```json
{
  "project": {
    "name": "string",
    "current_phase": "string"
  },
  "phases": [
    {
      "id": "string",
      "status": "not_started|in_progress|done|backlog",
      "progress": 0-100
    }
  ],
  "tasks": [
    {
      "id": "task-XXX",
      "status": "not_started|in_progress|blocked|done|backlog",
      "progress": 0-100,
      "subtasks": [
        {
          "id": "subtask-XXX-Y",
          "completed": boolean
        }
      ]
    }
  ],
  "session_history": [
    {
      "date": "YYYY-MM-DD",
      "session_number": integer,
      "summary": "string",
      "decisions": ["string"],
      "tasks_updated": ["task-XXX"],
      "next_session_goals": ["string"]
    }
  ],
  "metadata": {
    "last_updated": "ISO8601 timestamp",
    "version": "string"
  }
}
```

---

## Final Checklist Before Each Update

- [ ] Reviewed conversation for progress signals
- [ ] Updated task status and progress accurately
- [ ] Marked completed subtasks
- [ ] Recalculated phase progress
- [ ] Added session history entry
- [ ] Updated metadata.last_updated timestamp
- [ ] Verified no syntax errors in JSON

---

**Remember:** The tracker is Santiago's source of truth. Accuracy > speed.

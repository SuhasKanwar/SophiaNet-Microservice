# Tool session state

SophiaNet keeps an independent workspace for each tool in the current browser tab. Switching tools or visiting another section preserves drafts and completed results. This is frontend session state, separate from saved chat history.

## What is retained

| Workspace | Retained state |
| --- | --- |
| Learning Studio | Selected format, audience/difficulty, separate briefs and results for each format, quiz answers/review state/question position, flashcard position and revealed face |
| Research Papers | Topic, year filter, search results and AI relevance assessments |
| Diagrams | Prompt draft, generated Mermaid code; the SVG is rendered again when returning |
| YouTube | URL draft and the current tool-conversation reference |
| Notes | Current tool-conversation reference and selected files while the tab stays open |
| Chat landing and conversations | Independent input drafts and composer attachments; saved messages still load from the database |

Notes and composer `File` objects remain in memory only. They survive in-app navigation but must be reselected after refresh. Text/results are snapshotted to `sessionStorage`, scoped by signed-in user, and restored after refresh. Browser tabs have independent snapshots. No database schema or API change is required.

Learning Studio formats have separate state: a quiz remains intact when visiting flashcards and returning. A fresh generation replaces that format's previous result. Temporary loading/error indicators, active browser speech capture, canvas pan/zoom and expanded abstract details are not restored. Saved OCR/YouTube conversations remain available through ordinary chat history.

## Clearing policy

The sidebar provides **Reset tool** and **Clear all** controls, also available as labelled icons when collapsed. Both require confirmation. Reset clears only the current workspace, including Learning Studio's retained formats. Clear all clears retained tool workspaces and chat drafts in this tab. Neither deletes database chat history or files on the user's device. Export anything needed before clearing.

State expires after two hours without retained-state changes. Expiry is checked on initialization, window focus, and every minute while mounted. Signing out clears tool snapshots. Switching signed-in identities removes other users' tool snapshots from this tab. This does not synchronize state between devices or provide long-term saved notebooks.

A snapshot is limited to two million characters. If browser storage is blocked, full, or the snapshot is too large, the current workspace continues in memory and the sidebar indicates that browser snapshots are unavailable. Refresh then loses that memory-only workspace. Uploaded file contents are never serialized to session storage.

## Requests and resets

Navigating away cancels supported browser requests. Resetting a workspace remounts its tool, clears transient UI and aborts its current request. State setters carry an epoch: late responses from a reset or deactivated user session cannot repopulate cleared state. Cancellation is best effort for upstream AI work already running; it does not guarantee that provider computation stops. Tool-conversation creation already accepted by the server may remain in chat history even if later processing is cancelled.

## Verification

From `web`, run:

```bash
node --experimental-strip-types scripts/check-tool-session.mjs
```

This assert-based check covers refresh restoration, separate format state, memory-only file exclusion, scoped/all resets, stale writes, inactivity expiry, account isolation, corrupt snapshots and blocked storage. TypeScript and targeted lint pass.

Browser checks with a temporary signed session and mocked generation responses covered: quiz answers/index and per-format drafts across navigation/refresh, scoped reset preserving other tools, clear all, diagram and research result restoration, Notes file retention across navigation but exclusion on refresh, YouTube draft restoration, reset during an active search, mobile reset accessibility, and snapshot deletion on sign-out. Real provider generation, Google OAuth and backend tests were not repeated for this frontend state change.

# Ezra Nex AI Agent

Ezra Nex is a local-first, state-driven AI content system built to operate as a persistent digital persona.

Ezra generates:
- cinematic images
- controlled captions
- continuity-aware devlogs
- system-driven day posts

The project is designed around long-running internal state, not one-off content generation. Ezra tracks system behavior, tension, post mode, and content type over time, then expresses that through visuals and captions.

## Current Stable Direction

Ezra is currently running as a local-first system.

That means:
- generation happens on the local machine
- state and memory are stored locally
- posting is triggered locally
- Facebook publishing is direct
- Make is no longer part of the active posting pipeline

## Local Workflow

```text
Core
  ->
Daily Visual Manager
  ->
Visual
  ->
Renderer
  ->
Caption
  ->
Social Publishing
```

## Manual Runner Phases

`run_agent.bat` now executes Ezra in visible phases:

1. Core Agent
2. Visual Agent
3. Rendering Visual
4. Caption Agent
5. Social Publishing

This makes it easier to inspect failures quickly from CMD without guessing where the run stopped.

## Social Posting

Ezra currently posts directly to the Facebook Pages API.

Required local `.env` values:

```env
ANTHROPIC_API_KEY=
GEMINI_API_KEY=
FACEBOOK_PAGE_ID=
FACEBOOK_PAGE_ACCESS_TOKEN=
```

Primary posting path:
- `POST /{page-id}/photos`

Fallback path:
- `POST /{page-id}/feed`

If posting fails:
- the generated image remains saved locally
- the final caption remains saved locally
- the failure is logged clearly

## Devlog Behavior

Ezra supports structured devlog behavior centered around `NEX//THR`.

The current system can choose between:
- `devlog_post`
- `day_post`
- `hybrid`
- `system_visual`
- `silent`

Devlog captions are designed to feel like controlled build notes, not social-media commentary.

Typical devlog traits:
- restrained tone
- system-first language
- minimal emotional expression
- technical or observational phrasing
- gradual tension progression

When a post is a devlog, Ezra can append:
- `#devlog`

## Visual System

Ezra uses:
- Gemini image generation
- identity-locking with a reference image for Ezra-focused posts
- UI-only rendering rules for `system_visual` posts

Supported environment behavior includes:
- `system_core`
- `executive_hall`
- `surveillance_room`
- `data_vault`
- `dark_lab`
- `urban_exterior`
- `isolated_cafe`

Each environment shifts subtly based on:
- post mode
- devlog state
- system tension stage

## Current Stability Notes

This version includes:
- direct Facebook posting
- local-first execution
- content-type selection
- centralized Ezra personality rules
- stronger renderer retry behavior for empty Gemini image responses
- preserved local outputs on posting failure

Known operational reality:
- Facebook Page access tokens can expire
- Gemini can occasionally return temporary high-demand or empty-image responses
- local execution is currently more reliable than cloud deployment for Ezra's workflow

## Useful Local Commands

Run full visible cycle:

```cmd
cd /d "C:\Users\MalyMal25\Documents\Claude\Ezra Nex"
run_agent.bat
```

Run full silent cycle:

```cmd
cd /d "C:\Users\MalyMal25\Documents\Claude\Ezra Nex"
run_agent_silent.bat
```

Test only the social posting layer against the latest generated output:

```cmd
cd /d "C:\Users\MalyMal25\Documents\Claude\Ezra Nex"
python post_to_webhook.py
```

## Devlog Summary

Recent milestones:
- GitHub-backed version control stabilized
- Ezra personality and ideology layer expanded
- content-type logic added for devlogs, hybrids, silent posts, and system visuals
- direct Facebook posting replaced the old webhook route
- local phased runner updated to include a dedicated social publishing phase
- renderer hardened against Gemini empty-image responses

Recent lessons:
- cloud deployment added too much friction for the current workflow
- Facebook token expiration needs to be expected and managed
- local-first execution provides clearer debugging and better operational control

## Current Position

Ezra is no longer just generating outputs.

He now operates as a local, stateful content engine with:
- persistent continuity
- direct posting capability
- structured devlog behavior
- controlled system personality
- a clear path toward a future dashboard-based local application

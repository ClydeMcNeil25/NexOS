# Ezra Nex AI Agent

Ezra Nex is an autonomous, state-driven AI content system designed to simulate a persistent digital persona.

Built as a modular multi-agent pipeline, Ezra generates cinematic visuals and controlled captions while maintaining continuity across identity, environment, and narrative progression.

Rather than producing random content, Ezra operates as a structured system—tracking internal state, evolving over time, and expressing that evolution through subtle visual and textual outputs.

# Workflow (Brief Overview)

Ezra Nex operates through a multi-agent pipeline where each component is responsible for a specific stage of content generation.

## Ezra Nex System Workflow

```text
GitHub
  ↓
Railway deploys latest code
  ↓
Railway Cron triggers run_agent_auto.py
  ↓
run_agent_auto.py checks:
  - time window
  - duplicate posts
  - lock file
  ↓
Daily Visual Manager
  - chooses or keeps daily outfit
  - chooses allowed environments
  ↓
Core Agent
  - chooses post mode
  - chooses devlog state
  - chooses content type
  - generates Ezra signal
  ↓
Visual Agent
  - turns signal into image prompt
  - applies personality, environment, outfit, and content rules
  ↓
Renderer
  - generates image with Gemini
  - uses Ezra reference image unless system_visual
  - saves final 4:5 image
  ↓
Caption Agent
  - writes final caption
  - adds #devlog for devlog posts
  ↓
Webhook Delivery
  - sends image, caption, and metadata to Make
  ↓
Make
  - routes post to social platforms
```



---

Each cycle is state-driven, meaning every output is influenced by previous activity, system conditions, and long-term progression rather than isolated generation.

# Devlog v0.89a

# Devlog: Ezra Nex / NEX//THR Automation Milestone

Today marked a major systems milestone for Ezra Nex and the NEX//THR pipeline.

What started as a local multi-agent content workflow is now operating as a cloud-deployed autonomous system. The pipeline can generate a signal, produce a visual prompt, render an image, write a caption, and deliver the final post package through Make for social posting.

## What We Built

We moved Ezra from a local batch-script workflow into a Railway-hosted runtime connected to GitHub. The current pipeline now runs through:

Core Agent -> Daily Visual Manager -> Visual Agent -> Renderer -> Caption Agent -> Webhook Delivery

The system now supports:

- Cloud execution through Railway
- GitHub-based version control and deployment
- Make webhook delivery
- Image + caption payload delivery
- Daily visual continuity
- Devlog and day-post scheduling logic
- Controlled caption behavior
- Identity-locked rendering for Ezra
- Safety fallback behavior when the reference render fails
- Structured personality and ideology rules
- Early support for OS/UI-only NEX//THR system visuals

## Key Milestones

The first major milestone was getting Ezra fully version-controlled through GitHub. Once the repository was connected, Railway could rebuild directly from pushed commits instead of relying on the local machine.

The second milestone was getting Railway to run the automation wrapper correctly. The system now determines whether a post should run based on schedule windows, instead of needing manual local triggers.

The third milestone was Make integration. Ezra now sends the generated image, caption, metadata, and signal ID through a webhook. That payload successfully reached Make and was validated through a real social posting flow.

The fourth milestone was identity safety. We discovered that Gemini could occasionally fail when using Ezra’s character reference. Instead of allowing a prompt-only fallback that might generate the wrong person, we disabled that fallback for normal Ezra posts. If the identity-locked render fails, the system stops instead of posting an off-model Ezra.

The fifth milestone was personality expansion. Ezra’s ideology, behavior, environment rules, tension progression, caption logic, and post types were centralized into a dedicated personality layer. This gives the agents a stronger creative spine while keeping the output controlled and consistent.

The sixth milestone was adding real post-type logic. Ezra can now intentionally select between devlog posts, day posts, hybrid posts, silent posts, and system visual posts. This means NEX//THR can occasionally surface as UI fragments, logs, panels, node graphs, or graphical OS visuals instead of every image requiring Ezra in frame.

## Missteps / Lessons

The biggest early issue was assuming Railway would behave like the local machine. It did not. Environment variables, scheduled triggers, repo connection, and redeploy behavior all had to be clarified and tested.

Another issue was the Gemini renderer. We hit high-demand `503` errors and cases where Gemini returned no image parts. That led to retry/backoff handling and stricter failure behavior.

Make integration also had a few false starts. Sending image data as base64 was not enough for Facebook’s module. The solution was switching the webhook delivery to multipart file upload so Make could treat the image as an actual file buffer.

We also learned that giving Gemini the Ezra reference image during a UI-only system visual would conflict with the desired output. The renderer now skips the character reference only for `system_visual` posts.

## Current State

Ezra is no longer just generating isolated content.

The system now has:

- Autonomy
- Scheduling logic
- Cloud deployment
- Webhook delivery
- Social posting integration
- Memory and run history
- Visual continuity
- Personality rules
- Post-type selection
- Identity protection
- NEX//THR system visual support

This is the first version that feels like a real autonomous content engine rather than a collection of scripts.

The next phase is refinement: improving post quality, tuning frequency, expanding NEX//THR visual language, and making Ezra’s system tension evolve more deliberately over time.

# Ezra Nex Railway Deployment

## Command

Use this command for the Railway service or scheduled job:

```bash
python run_agent_auto.py
```

## Required Environment Variables

- `ANTHROPIC_API_KEY`
- `GEMINI_API_KEY` or `GOOGLE_API_KEY`

## Optional Environment Variables

- `MAKE_WEBHOOK_URL`
- `TZ=America/Chicago`
- `EZRA_FORCE_POST_MODE=day_post` or `EZRA_FORCE_POST_MODE=devlog`

If `MAKE_WEBHOOK_URL` is not set, Ezra still completes the local/cloud generation cycle and skips delivery.

Set `TZ=America/Chicago` so the day post and devlog windows match your local schedule.

Use `EZRA_FORCE_POST_MODE` only for deployment testing. Remove it after verification so Ezra returns to schedule-based automation.

Valid force values:

- `morning_post`
- `afternoon_post`
- `day_post`
- `devlog`

## Production Schedule

Ezra now supports three daily slots with duplicate protection:

- Morning post: 9:00 AM to before 12:00 PM
- Afternoon post: 2:00 PM to before 5:00 PM
- Devlog: 9:00 PM or later

Recommended Railway cron for production:

```bash
python run_agent_auto.py
```

Run it every 15-30 minutes. Ezra will skip automatically when no slot is active or when that slot already completed today.

## Notes

- Do not upload `.env` to GitHub or Railway.
- Railway environment variables replace `.env`.
- Runtime files such as generated images, captions, prompts, and lock files are ignored by Git after this setup.

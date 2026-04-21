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

If `MAKE_WEBHOOK_URL` is not set, Ezra still completes the local/cloud generation cycle and skips delivery.

Set `TZ=America/Chicago` so the day post and devlog windows match your local schedule.

## Notes

- Do not upload `.env` to GitHub or Railway.
- Railway environment variables replace `.env`.
- Runtime files such as generated images, captions, prompts, and lock files are ignored by Git after this setup.

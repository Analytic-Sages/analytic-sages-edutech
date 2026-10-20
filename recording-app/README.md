# Analytic Sages content-first classroom recorder

This is a standalone RealtimeKit custom recording app. It records only the lesson content, not the normal classroom chrome.

## Layout behavior

- Screen share active: the shared screen fills the entire recording canvas.
- No screen share: show the pinned/active speaker, then the first participant with video.
- No participant available: show a neutral waiting slate.
- Participant audio is retained.
- The RealtimeKit recording SDK controls the recorder lifecycle.

## Deploy

Prerequisites: Node.js 20+, a Cloudflare account, and Wrangler authorization.

```bash
npm install
npx wrangler login
npm run deploy
```

Use the HTTPS URL printed by Wrangler as `REALTIMEKIT_RECORDING_APP_URL` in the backend service's environment (Render). Do not append `authToken` or `config`; RealtimeKit adds those itself. Redeploy the backend after setting the variable.

Before enabling this in production, ensure the RealtimeKit app has a `recorder_preset_v2` preset with both `is_recorder=true` and `hidden_participant=true`. Test a class with screen share start/stop transitions and verify the output file's resolution and audio.

The renderer intentionally uses a minimal UI. Never put API keys, Cloudflare tokens, or static participant tokens in this app; RealtimeKit supplies a short-lived recorder token in the URL.

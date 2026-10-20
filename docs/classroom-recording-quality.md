# Live classroom recording quality

## What the application now configures

New RealtimeKit meetings request a composite recording profile of **1920×1080 (1080p), H.264 video, and AAC stereo audio**. These are sent as per-meeting recording_config values, which take precedence over RealtimeKit app-level defaults. The automatic record_on_start behavior remains enabled; the app does not switch to a manual-only recording flow.

The defaults can be adjusted through backend environment variables:

- REALTIMEKIT_RECORDING_VIDEO_WIDTH — default 1920, valid range 1–1920.
- REALTIMEKIT_RECORDING_VIDEO_HEIGHT — default 1080, valid range 1–1920.
- REALTIMEKIT_RECORDING_VIDEO_CODEC — default H264; allowed values H264, VP8, or VP9.

Set these in the backend hosting environment (for example, Render), then redeploy the backend. These settings apply to **new meetings**; they do not re-encode recordings that already exist.

The explicit recording helper also uses the documented POST /accounts/{account_id}/realtime/kit/{app_id}/recordings endpoint and sends the same video/audio profile. Normal classroom meetings continue to use automatic recording, so do not call the explicit helper in parallel with an active recording.

## Content-first layout (custom recording app)

The repository now includes a separate RealtimeKit recording renderer in `recording-app/`. It deliberately does not render the meeting UI:

- While a screen is shared, the shared content fills the complete 16:9 recording frame; chat, participant gallery, controls, and browser meeting chrome are not rendered.
- When screen sharing stops, the renderer falls back to the active/pinned speaker, then a participant video. If no one has joined yet, it displays a neutral waiting screen.
- It preserves participant audio and keeps the 1920×1080 H.264 / AAC stereo recording profile.
- When `REALTIMEKIT_RECORDING_APP_URL` is configured in the backend, default automatic recording is disabled for new meetings. The backend starts the custom recorder when an instructor/staff member joins, rather than starting an empty recording when the first student arrives.

### Deploy and activate the custom renderer

1. Deploy the standalone app from `recording-app/` to Cloudflare Workers/Static Assets:
   ```bash
   cd recording-app
   npm install
   npx wrangler login
   npm run deploy
   ```
2. Use the resulting public HTTPS URL as `REALTIMEKIT_RECORDING_APP_URL` in the **backend** hosting environment (Render), with no `authToken` or `config` query string. Redeploy the backend after setting it.
3. Confirm the RealtimeKit app has a `recorder_preset_v2` preset with `is_recorder=true` and `hidden_participant=true`; do not remove `is_recorder`.
4. Run a short instructor-led test class. Share a full screen, stop sharing, then resume sharing. Verify the recording switches automatically between screen content and instructor view, and check audio sync and 1920×1080 output before using it for a real class.

Until the custom app is deployed and its URL is configured on the backend, the existing default RealtimeKit recording behavior remains active. The code change alone does not deploy the renderer or activate the URL.

## Cloudflare dashboard checks still required

1. Open **Cloudflare Dashboard → RealtimeKit → your application**.
2. Confirm recording is enabled for the application and the app has a valid recording storage configuration. Cloudflare documents that record_on_start requires storage configuration in the Developer Portal; without it, automatic recording may not produce the expected downloadable file.
3. Set the app-level recording fallback to **H.264, 1920×1080** if those controls are available in your app's recording settings. The application sends per-meeting settings for newly created meetings, but app-level defaults still matter for any meetings created elsewhere or any provider-side paths that omit overrides.
4. Confirm the RealtimeKit API token has the **Realtime** or **Realtime Admin** permission required by the recording APIs.
5. Keep the recording archive path configured. RealtimeKit download URLs expire after about seven days; the existing backend pipeline copies recordings into permanent Cloudflare Stream and/or private R2 storage. Verify those credentials and storage are healthy.

## Instructor capture checklist

- Share the **entire screen or the specific application window**, not a browser tab showing a scaled-down desktop, when teaching code, SQL, notebooks, or dashboards.
- Before teaching, set the editor/terminal zoom large enough to read at 1080p and close irrelevant panels.
- Prefer a stable wired connection where possible. 1080p output can increase file size and processing time compared with 720p.
- Make a short test class, then verify the resulting file is actually 1920×1080, audio is synchronized, screen text is readable at normal playback, and the archived copy opens after the temporary RealtimeKit URL expires.

## Important limits

Higher output resolution cannot restore detail that was never captured in the source screen share, and it does not force a presenter's device or browser to share at 1080p. The RealtimeKit participant preset and SDK/browser capture behavior still influence the source. Review the instructor preset in the RealtimeKit Developer Portal if screen-share source quality remains low. Existing recordings require a new recording or a provider-supported re-encode; changing these settings will not improve their original pixels.

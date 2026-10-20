# Live classroom recording quality

## What the application now configures

New RealtimeKit meetings request a composite recording profile of **1920×1080 (1080p), H.264 video, and AAC stereo audio**. These are sent as per-meeting recording_config values, which take precedence over RealtimeKit app-level defaults. The automatic record_on_start behavior remains enabled; the app does not switch to a manual-only recording flow.

The defaults can be adjusted through backend environment variables:

- REALTIMEKIT_RECORDING_VIDEO_WIDTH — default 1920, valid range 1–1920.
- REALTIMEKIT_RECORDING_VIDEO_HEIGHT — default 1080, valid range 1–1920.
- REALTIMEKIT_RECORDING_VIDEO_CODEC — default H264; allowed values H264, VP8, or VP9.

Set these in the backend hosting environment (for example, Render), then redeploy the backend. These settings apply to **new meetings**; they do not re-encode recordings that already exist.

The explicit recording helper also uses the documented POST /accounts/{account_id}/realtime/kit/{app_id}/recordings endpoint and sends the same video/audio profile. Normal classroom meetings continue to use automatic recording, so do not call the explicit helper in parallel with an active recording.

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

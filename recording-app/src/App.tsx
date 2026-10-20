import { useEffect, useRef, useState } from "react";
import { RealtimeKitProvider, useRealtimeKitClient } from "@cloudflare/realtimekit-react";
import { RealtimeKitRecording } from "@cloudflare/realtimekit-recording-sdk";
import RecordingView from "./RecordingView";

function RecorderApp() {
  const [meeting, initMeeting] = useRealtimeKitClient();
  const [error, setError] = useState<string | null>(null);
  const initialized = useRef(false);

  useEffect(() => {
    if (initialized.current) return;
    initialized.current = true;
    let cancelled = false;

    async function initialize() {
      try {
        const params = new URLSearchParams(window.location.search);
        const authToken = params.get("authToken");
        if (!authToken) {
          throw new Error("RealtimeKit did not provide the recording authorization token.");
        }

        const baseURI = params.get("baseURI") ?? "realtime.cloudflare.com";
        const client = await initMeeting({
          authToken,
          baseURI,
          defaults: { audio: false, video: false },
        });
        if (cancelled || !client) return;

        // RealtimeKit's recording SDK manages the recorder lifecycle and its
        // connection to the recording container. Keep autoStart/autoStop defaults.
        const recording = new RealtimeKitRecording({});
        await recording.init(client);
      } catch (cause) {
        if (!cancelled) {
          setError(cause instanceof Error ? cause.message : "Unable to initialize recording.");
        }
      }
    }

    void initialize();
    return () => { cancelled = true; };
  }, [initMeeting]);

  if (error) {
    return <main className="error-screen"><h1>Recording could not start</h1><p>{error}</p></main>;
  }

  return (
    <RealtimeKitProvider value={meeting} fallback={<main className="waiting">Preparing recording…</main>}>
      <RecordingView />
    </RealtimeKitProvider>
  );
}

export default function App() {
  return <RecorderApp />;
}
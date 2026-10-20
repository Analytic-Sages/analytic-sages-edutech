import {
  RtkAvatar,
  RtkParticipantTile,
  RtkParticipantsAudio,
  RtkScreenshareView,
} from "@cloudflare/realtimekit-react-ui";
import { useRealtimeKitMeeting, useRealtimeKitSelector } from "@cloudflare/realtimekit-react";

export default function RecordingView() {
  const { meeting } = useRealtimeKitMeeting();
  const joinedParticipants = useRealtimeKitSelector((client) => client.participants.joined.toArray());
  const activeParticipants = useRealtimeKitSelector((client) => client.participants.active.toArray());
  const pinnedParticipants = useRealtimeKitSelector((client) => client.participants.pinned.toArray());

  // Ignore hidden recorder participants and prefer a real screen share whenever
  // one is active. This keeps chat, participant rails, and meeting controls out.
  const visibleParticipants = joinedParticipants.filter((p) => !(p as { isRecorder?: boolean }).isRecorder);
  const screensharer = visibleParticipants.find((p) => p.screenShareEnabled);
  const pinned = pinnedParticipants.find((p) => visibleParticipants.some((v) => v.id === p.id));
  const activeSpeaker = pinned
    ?? activeParticipants.find((p) => visibleParticipants.some((v) => v.id === p.id))
    ?? visibleParticipants.find((p) => p.videoEnabled)
    ?? visibleParticipants[0];

  return (
    <main className="recording-canvas">
      {screensharer ? (
        <section className="content-frame" aria-label="Shared screen">
          <RtkScreenshareView meeting={meeting} participant={screensharer} hideFullScreenButton />
        </section>
      ) : activeSpeaker ? (
        <section className="speaker-frame" aria-label="Instructor or active speaker">
          <RtkParticipantTile participant={activeSpeaker}>
            <RtkAvatar participant={activeSpeaker} />
          </RtkParticipantTile>
        </section>
      ) : (
        <section className="empty-frame" aria-label="Waiting for instructor">
          <div className="brand-mark">AS</div>
          <p>Waiting for the instructor to begin</p>
        </section>
      )}
      <RtkParticipantsAudio meeting={meeting} />
    </main>
  );
}
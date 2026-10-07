from app.services.realtimekit import stale_participant_ids


def test_rejoin_removes_every_older_seat_for_the_same_person():
    participants = [
        {"id": "old-seat", "custom_participant_id": "user-1"},
        {"id": "new-seat", "custom_participant_id": "user-1"},
        {"id": "other", "custom_participant_id": "user-2"},
    ]
    assert stale_participant_ids(participants, "user-1", keep_id="new-seat") == ["old-seat"]


def test_conflict_clears_every_seat_before_a_fresh_join():
    participants = [
        {"id": "ghost", "customParticipantId": "user-1"},
        {"id": "second-ghost", "custom_participant_id": "user-1"},
    ]
    assert stale_participant_ids(participants, "user-1", keep_id=None) == [
        "ghost",
        "second-ghost",
    ]

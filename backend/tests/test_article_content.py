from app.services.article_content import validate_body


def test_long_report_paragraph_is_accepted():
    text = ("Blockchain data pipelines need warehouses, transforms, and deployment. " * 800).strip()
    assert len(text) > 20_000
    body = validate_body({"version": 1, "blocks": [{"type": "paragraph", "text": text}]})
    joined = " ".join(block["text"] for block in body["blocks"])
    assert body["blocks"][0]["type"] == "paragraph"
    assert "Blockchain data pipelines" in joined
    assert len(joined) >= len(text) - 5


def test_report_longer_than_one_block_is_split_not_rejected():
    sentence = "Section of the research report. "
    text = sentence * 12_000
    assert len(text) > 200_000
    body = validate_body({"version": 1, "blocks": [{"type": "paragraph", "text": text}]})
    assert len(body["blocks"]) > 1
    assert all(block["type"] == "paragraph" for block in body["blocks"])
    assert all(len(block["text"]) <= 200_000 for block in body["blocks"])
    assert "".join(block["text"] for block in body["blocks"]).startswith("Section of the research report.")

import pytest
from fastapi import HTTPException

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


def test_many_paragraphs_are_accepted():
    blocks = [{"type": "paragraph", "text": f"Paragraph {index} of the research report."} for index in range(250)]
    body = validate_body({"version": 1, "blocks": blocks})
    assert len(body["blocks"]) == 250


def test_long_list_item_and_heading_are_accepted():
    item = ("The protocol collected more fees than the previous quarter. " * 80).strip()
    assert len(item) > 2_000
    heading = (
        "How onchain fees, active addresses, and bridge volume changed across the quarter. " * 6
    ).strip()
    assert len(heading) > 300
    body = validate_body(
        {
            "version": 1,
            "blocks": [
                {"type": "heading", "level": 2, "text": heading},
                {"type": "list", "ordered": False, "items": [item] * 60},
                {"type": "takeaways", "items": [item]},
            ],
        }
    )
    assert body["blocks"][0]["text"] == heading
    assert len(body["blocks"][1]["items"]) == 60
    assert body["blocks"][2]["items"][0].startswith("The protocol")


def test_over_limit_names_the_block():
    with pytest.raises(HTTPException) as exc:
        validate_body({"version": 1, "blocks": [{"type": "heading", "level": 2, "text": "h" * 6_000}]})
    assert exc.value.detail == "A heading is too long"

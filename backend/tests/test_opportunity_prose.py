from __future__ import annotations

from app.services.opportunity_prose import html_to_markdown, normalize_description


def test_html_job_description_keeps_headings_and_lists():
    html = """
    <div>
      <h2>About us</h2>
      <p>Phantom is a modern money app used by millions of people.</p>
      <script>alert(1)</script>
      <h2>Responsibilities:</h2>
      <ul>
        <li>Manage releases</li>
        <li>Coordinate stakeholders</li>
      </ul>
      <h3>Requirements</h3>
      <ol>
        <li>5+ years experience</li>
        <li>Strong communication skills</li>
      </ol>
    </div>
    """
    markdown = html_to_markdown(html)
    assert "alert" not in markdown
    assert "## About us" in markdown
    assert "Phantom is a modern money app" in markdown
    assert "- Manage releases" in markdown
    assert "- Coordinate stakeholders" in markdown
    assert "## Responsibilities" in markdown or "### Responsibilities" in markdown
    assert "1. 5+ years experience" in markdown


def test_plain_text_promotes_section_headings_and_bullets():
    text = """About us
Phantom is a modern money app.

What you'll do
- Manage releases
- Coordinate stakeholders

Requirements:
* 5+ years experience
* Strong communication skills
"""
    markdown = normalize_description(text)
    assert "### About us" in markdown
    assert "### What you'll do" in markdown or "### What you" in markdown
    assert "- Manage releases" in markdown
    assert "- 5+ years experience" in markdown


def test_collapsed_text_splits_known_headings():
    text = (
        "Phantom is a modern money app used by millions. About us Phantom builds "
        "simple products. Responsibilities Manage releases across teams. "
        "Requirements Five or more years of experience."
    )
    markdown = normalize_description(text)
    assert "### About us" in markdown
    assert "### Responsibilities" in markdown
    assert "### Requirements" in markdown
    assert "Phantom is a modern money app" in markdown


def test_markdown_passthrough_is_stable():
    source = "### About the role\n\nWe need a data engineer.\n\n- Write SQL\n- Ship dashboards"
    assert normalize_description(source) == source


def test_greenhouse_parser_preserves_list_structure():
    from app.models.opportunity import OpportunitySource
    from app.services.opportunity_sources.greenhouse import parse_jobs

    source = OpportunitySource(name="Phantom", connector_type="greenhouse", config={"board_token": "phantom"})
    items = parse_jobs(
        {
            "jobs": [
                {
                    "id": 1,
                    "title": "Release Manager",
                    "absolute_url": "https://boards.greenhouse.io/phantom/jobs/1",
                    "location": {"name": "Remote"},
                    "content": "<h2>About us</h2><p>Phantom is a money app.</p><ul><li>Manage releases</li></ul>",
                }
            ]
        },
        source,
    )
    assert len(items) == 1
    assert "## About us" in items[0].description
    assert "- Manage releases" in items[0].description
    assert "\n" in items[0].description

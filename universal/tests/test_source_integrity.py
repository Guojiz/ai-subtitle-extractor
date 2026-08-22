"""Source-caption integrity before editorial article conversion."""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

from lib.clean import (
    cues_to_paragraphs,
    paragraphs_to_text,
    source_cue_coverage_report,
)
from lib.models import Cue, ExtractResult, TrackInfo


cues = [
    Cue(start=0, end=1, text="Well"),
    Cue(start=1, end=2, text="um"),
    Cue(start=2, end=3, text="this repeats"),
    Cue(start=3, end=4, text="this repeats"),
    Cue(start=4, end=5, text="重要数字 42"),
]
source_text = paragraphs_to_text(cues_to_paragraphs(cues))
coverage = source_cue_coverage_report(cues, source_text)
assert coverage["complete"], coverage

result = ExtractResult(
    ok=True,
    platform="test",
    adapter="test",
    url="https://example.test/video",
    title="Source Integrity",
    language="en",
    track=TrackInfo(language="en", kind="human", source="fixture"),
    cues=cues,
    plain_text=source_text,
)
payload = result.to_dict()
assert payload["source_coverage"]["complete"]
assert payload["requires_editorial_pass"] is True
assert payload["plain_text"] == source_text

# Source capture keeps filler for audit; the editorial Agent, not the extractor,
# decides that it is non-substantive and removes it from the final article.
assert "um" in source_text
assert source_text.count("this repeats") == 2

print("SOURCE_INTEGRITY_OK", coverage)

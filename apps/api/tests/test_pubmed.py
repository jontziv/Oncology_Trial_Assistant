from copilot.clients.pubmed import _map_summaries


def test_pubmed_summary_mapping_preserves_citation_identity() -> None:
    publications, sources = _map_summaries(
        {
            "result": {
                "123": {
                    "title": "A phase II NSCLC study.",
                    "fulljournalname": "Journal of Thoracic Oncology",
                    "pubdate": "2025",
                    "authors": [{"name": "Example A"}],
                }
            }
        },
        ["123"],
    )

    assert publications[0].source_id == "PUBMED:123"
    assert publications[0].title == "A phase II NSCLC study"
    assert sources[0].record_id == "123"

from demos.evaluate_general_retrieval import (
    first_expected_title_rank,
    split_expected_titles,
    summarize_rows,
)


def test_expected_title_options_and_rank_are_case_insensitive():
    expected = split_expected_titles("Khan et al. - 2017 | Patel et al. - 2019")
    titles = ["Unrelated paper", "KHAN ET AL. - 2017 - Vertical bifacial solar farms"]
    assert expected == ["Khan et al. - 2017", "Patel et al. - 2019"]
    assert first_expected_title_rank(titles, expected) == 2


def test_missing_expected_title_has_no_rank():
    assert first_expected_title_rank(["Unrelated paper"], ["Expected paper"]) is None


def test_summary_excludes_failed_queries_from_retrieval_metrics():
    rows = [
        {"error": "", "first_relevant_rank": 1, "latency_ms": 100},
        {"error": "", "first_relevant_rank": None, "latency_ms": 300},
        {"error": "database unavailable", "first_relevant_rank": None, "latency_ms": 10},
    ]
    summary = summarize_rows(rows)
    assert summary == {
        "cases": 3,
        "successful_queries": 2,
        "source_hit_at_k": 0.5,
        "mean_first_relevant_rank": 1,
        "median_latency_ms": 200,
        "mean_latency_ms": 200,
    }

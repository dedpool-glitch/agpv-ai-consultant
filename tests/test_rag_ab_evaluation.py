from demos.run_rag_ab_evaluation import histories_before_each_row, select_case_indices


def test_selects_explicit_unique_general_questions():
    rows = [
        {
            "turn_type": "general_question",
            "question": "How does spacing affect yield?",
            "error": "",
            "include_for_evaluation": "yes",
        },
        {
            "turn_type": "general_question",
            "question": "  how does spacing affect yield? ",
            "error": "",
            "include_for_evaluation": "yes",
        },
        {
            "turn_type": "run_pvmaps",
            "question": "Run an estimate",
            "error": "",
            "include_for_evaluation": "yes",
        },
    ]

    assert select_case_indices(rows, limit=10) == [0]


def test_history_contains_only_prior_turns_in_same_session():
    rows = [
        {"session_id": "a", "question": "Q1", "answer": "A1"},
        {"session_id": "b", "question": "Other", "answer": "Other answer"},
        {"session_id": "a", "question": "Q2", "answer": "A2"},
    ]

    histories = histories_before_each_row(rows)

    assert histories[0] == []
    assert histories[1] == []
    assert histories[2] == [
        {"role": "user", "content": "Q1"},
        {"role": "assistant", "content": "A1"},
    ]

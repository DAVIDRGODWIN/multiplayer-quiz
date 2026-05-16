from app.services.scoring import calculate_score


def test_instant_answer_scores_max():
    assert calculate_score(30, 0) == 100


def test_halfway_scores_fifty():
    assert calculate_score(30, 15) == 50


def test_at_limit_scores_zero():
    assert calculate_score(30, 30) == 0


def test_after_limit_scores_zero():
    assert calculate_score(30, 35) == 0


def test_proportional_reduction():
    # 10s elapsed on a 30s question → (30-10)/30 = 66.67 → rounds to 67
    assert calculate_score(30, 10) == 67

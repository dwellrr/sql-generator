from app.llm import is_valid_syntax


def test_valid_syntax():
    assert is_valid_syntax("SELECT id FROM users WHERE age > 30") == True


def test_invalid_syntax():
    assert is_valid_syntax("SELECT FROM WHERE") == False

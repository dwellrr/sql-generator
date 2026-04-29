import pytest
from unittest.mock import Mock
from sqlalchemy.orm import Session

from app.services.llm_service import LLMService


@pytest.fixture
def fake_db():
    return Mock(spec=Session)


@pytest.fixture
def llm_service(fake_db):
    return LLMService(db=fake_db)


def test_valid_syntax(llm_service):
    assert llm_service.is_valid_syntax("SELECT id FROM users WHERE age > 30") is True


def test_invalid_syntax(llm_service):
    assert llm_service.is_valid_syntax("SELECT FROM WHERE") == False


def test_clean_sql(llm_service):
    assert (
        llm_service.clean_sql("```sql SELECT id FROM users WHERE age > 30```")
        == "SELECT id FROM users WHERE age > 30"
    )

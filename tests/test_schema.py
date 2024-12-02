"""Test the schemas of the various config.json section."""

from typing import Any
from typing import Dict
from typing import Generator
from typing import Tuple
from typing import Type
from typing import Union

import pytest

from tests.schema import Config
from tests.schema import Question
from tests.schema import Schema
from tests.schema import SelectBoxOptions


def base_schema_check(
    data: Dict[str, Any], schema: Type[Schema], expected_result: bool
) -> None:
    """Central testing logic for schemas."""
    if expected_result:
        # the question is expected to be valid
        try:
            schema_obj = schema(**data)
            assert schema_obj is not None
        except (TypeError, ValueError):
            pytest.fail("Unexpected error raised for valid question data")
    else:
        # the question is expected to be invalid
        with pytest.raises((TypeError, ValueError)):
            _ = schema(**data)


def selectbox_option_test_data() -> (
    Generator[Tuple[Dict[str, Union[bool, str]], bool], None, None]
):
    """Generates all possible test data for testing selectbox options schema."""
    # valid selectbox option
    yield {
        "label": "Option 1",
        "value": "option1",
        "selected": True,
        "disabled": False,
    }, True

    # valid selectbox option with defaults
    yield {"label": "Option 2", "value": "option2"}, True

    # invalid selectbox option: wrong field types
    yield {"label": "Option 3", "value": "option3", "selected": "true"}, False
    yield {"label": "Option 4", "value": "option4", "disabled": "false"}, False

    # invalid selectbox option: missing required keys
    yield {"label": "Option 5"}, False
    yield {"value": "option6"}, False

    # invalid selectbox option: wrong key name
    yield {"label": "Option 7", "val": "option7"}, False
    yield {
        "label": "Option 8",
        "value": "option8",
        "selected": True,
        "disbled": False,
    }, False


@pytest.mark.schema
@pytest.mark.parametrize("option_data, expected_result", selectbox_option_test_data())
def test_selectbox_option_schema_class(
    option_data: Dict[str, Any], expected_result: bool
) -> None:
    """Tests that every selectbox option conforms to expected result."""
    base_schema_check(option_data, SelectBoxOptions, expected_result)


def question_test_data() -> Generator[Tuple[Dict[str, Any], bool], None, None]:
    """Generates all possible test data for testing question schema."""
    # valid question
    yield {
        "label": "Question 1",
        "name": "question1",
        "type": "text",
        "required": True,
        "custom": {"placeholder": "Enter your answer here"},
    }, True

    # valid question with selectbox type
    yield {
        "label": "Question 2",
        "name": "question2",
        "type": "selectbox",
        "required": True,
        "options": [{"label": "Option 1", "value": "option1"}],
    }, True

    # invalid question: selectbox type with missing options
    yield {
        "label": "Question 3",
        "name": "question3",
        "type": "selectbox",
        "required": True,
    }, False

    # invalid question: missing type
    yield {
        "label": "Question 4",
        "name": "question4",
        "required": True,
    }, False

    # invalid question: incorrect type
    yield {
        "label": "Question 5",
        "name": "question5",
        "type": 3.1415926535897932384626433832795028841971,  # nees string
        "required": True,
    }, False

    # invalid question: only string type allowed in multiline list string label
    yield {
        "label": [
            "This is question 6",
            3.1415926535897932384626433832795028841971,
            "and it is a multiline string,",
            "but it should only have strings",
            "and no other type",
        ],
        "name": "question1",
        "type": "text",
        "required": True,
        "custom": {"placeholder": "Enter your answer here"},
    }, False


@pytest.mark.schema
@pytest.mark.parametrize("question_data, expected_result", question_test_data())
def test_question_schema_class(
    question_data: Dict[str, Any], expected_result: bool
) -> None:
    """Tests the data provided by the question_test_data generator."""
    base_schema_check(question_data, Question, expected_result)


@pytest.mark.schema
def test_question_warning() -> None:
    """Tests that a warning is generated for valid (but not recommended) question."""
    # test data
    question_data = {
        "label": "Question 4",
        "name": "question4",
        "type": "text",
        "required": True,
        "options": [{"label": "Option 1", "value": "option1"}],
    }

    # warning message
    expected_warning_message = "Options can only be used by selectbox question type."

    # capture warning
    with pytest.warns(UserWarning, match=expected_warning_message) as warning_info:
        question = Question(**question_data)  # type: ignore

    # run asserts
    assert len(warning_info) == 1
    assert question.options is not None
    if isinstance(warning_info[0].message, Warning):
        assert warning_info[0].message.args[0] == expected_warning_message


def config_test_data() -> Generator[Tuple[Dict[str, Any], bool], None, None]:
    """Generates all possible test data for testing config schema."""
    # valid config with one question
    yield {
        "email": "example@example.com",
        "title": "Title",
        "form_backend_url": "http://example.com/form",
        "subject": "Subject",
        "questions": [
            {
                "label": "Question 1",
                "name": "question1",
                "type": "text",
                "required": True,
                "custom": {"placeholder": "Enter your answer here"},
            }
        ],
    }, True

    # valid config with multiple questions
    yield {
        "email": "example@example.com",
        "title": "Title",
        "subject": "Subject",
        "questions": [
            {
                "label": "Question 2",
                "name": "question2",
                "type": "text",
                "required": True,
                "custom": {"placeholder": "Enter your answer here"},
            },
            {
                "label": "Question 3",
                "name": "question3",
                "type": "selectbox",
                "required": True,
                "options": [{"label": "Option 1", "value": "option1"}],
            },
        ],
    }, True

    # invalid config: missing required questions
    yield {
        "email": "example@example.com",
        "title": "Title",
        "subject": "Subject",
        "form_backend_url": "http://example.com/form",
    }, False

    # invalid config: wrong data types
    yield {
        "email": "example@example.com",
        "title": "Title",
        "subject": "Subject",
        "form_backend_url": 2.718281828459045235360287471352662497757,  # needs string
        "questions": [
            {
                "label": "Question 4",
                "name": "question4",
                "type": "text",
                "required": True,
                "custom": {"placeholder": "Enter your answer here"},
            }
        ],
    }, False

    # invalid config: wrong type for questions
    yield {
        "email": "example@example.com",
        "title": "Title",
        "subject": "Subject",
        "form_backend_url": "http://example.com/form",
        "questions": "invalid",  # string instead of list
    }, False

    # invalid config: number cannot be in multiline instructions
    yield {
        "instructions": ["All work", 2, "and no play", "make jack", "a dull", "boy"],
        "email": "example@example.com",
        "title": "Title",
        "subject": "Subject",
        "form_backend_url": "http://example.com/form",
        "questions": [
            {
                "label": "Question 5",
                "name": "question5",
                "type": "text",
                "required": True,
                "custom": {"placeholder": "Enter your answer here"},
            }
        ],
    }, False

    # invalid config: one target (either email or form backend) must be set
    yield {
        "title": "Title",
        "subject": "Subject",
        "questions": [
            {
                "label": "Question 6",
                "name": "question6",
                "type": "text",
                "required": True,
                "custom": {"placeholder": "Enter your answer here"},
            }
        ],
    }, False

    # invalid config: questions have the same "name" attribute
    yield {
        "email": "example@example.com",
        "title": "Title",
        "form_backend_url": "http://example.com/form",
        "subject": "Subject",
        "questions": [
            {
                "label": "Question 7",
                "name": "question7",
                "type": "text",
                "required": True,
                "custom": {"placeholder": "Enter your answer here"},
            },
            {
                "label": "Question 8",
                "name": "question7",
                "type": "number",
                "required": True,
            },
        ],
    }, False


@pytest.mark.schema
@pytest.mark.parametrize("config_data, expected_result", config_test_data())
def test_config_schema_class(
    config_data: Dict[str, Any], expected_result: bool
) -> None:
    """Tests the data provided by the question_test_data generator."""
    base_schema_check(config_data, Config, expected_result)

import pytest
import os
from dotenv import load_dotenv
from llm.parameter_extractor import extract_questionnaire_parameter


@pytest.fixture
def api_key():
    load_dotenv()
    key = os.getenv("PURDUE_GENAI_KEY")
    if not key:
        pytest.skip("PURDUE_GENAI_KEY is not set.")
    return key


@pytest.mark.integration
def test_pitch_response(api_key):
    question="What is the pitch of the solar panel array?"
    field="pitch"
    response="I would want the rows to be atleast ten meters apart to allow for maintenance access."
    extracted_response=extract_questionnaire_parameter(field,question,response,api_key)
    assert extracted_response["field"]==field
    assert extracted_response["value"]==10

@pytest.mark.integration
def test_azimuth_response(api_key):
    question="What is the azimuth orientation of the solar panel array?"
    field="azimuth"
    response="The rows run east-west."
    extracted_response=extract_questionnaire_parameter(field,question,response,api_key)
    assert extracted_response["field"]==field
    assert extracted_response["value"]==90

@pytest.mark.integration
def test_array_config_response(api_key):
    question="What is the array configuration of the solar panel array?"
    field="array_config"
    response="I want my solar panel array to track the sun throughout the day."
    extracted_response=extract_questionnaire_parameter(field,question,response,api_key)
    assert extracted_response["field"]==field
    assert extracted_response["value"]=="tracking"

@pytest.mark.integration
def test_unknown_response(api_key):
    question="What is the tilt of the solar panel array?"
    field="tilt"
    response="I'm not sure."
    extracted_response=extract_questionnaire_parameter(field,question,response,api_key)
    assert extracted_response["field"]==field
    assert extracted_response["value"] is None

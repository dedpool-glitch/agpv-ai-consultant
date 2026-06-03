from constants import NUMERIC_QUESTIONNAIRE_FIELDS


def parse_questionnaire_answer(field, value):
    if field in NUMERIC_QUESTIONNAIRE_FIELDS:
        return float(value)

    return value

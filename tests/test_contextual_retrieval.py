import copy
import json
import pytest
from llm.rag_source_router import decide_rag_source, plan_expert_retrieval
from llm.retrieval_query import recent_text_history

HISTORY = [{'role': 'user', 'content': 'Explain bifacial energy gain.'},
           {'role': 'assistant', 'content': 'It compares bifacial yield with optimal monofacial yield.'}]


def mock_plan(monkeypatch, **fields):
    monkeypatch.setattr('llm.rag_source_router.call_llm', lambda *_: json.dumps(dict(source='both', **fields)))


def test_followup_resolved_and_original_history_unchanged(monkeypatch):
    history = copy.deepcopy(HISTORY)
    mock_plan(monkeypatch, query_mode='contextual', retrieval_query='What is the denominator of bifacial energy gain?')
    result = decide_rag_source('What is its denominator?', 'key', history)
    assert result['retrieval_query'] == 'What is the denominator of bifacial energy gain?'
    assert result['source'] == 'both'
    assert history == HISTORY


@pytest.mark.parametrize('mode', ['standalone', 'ambiguous'])
def test_independent_or_ambiguous_never_accepts_model_rewrite(monkeypatch, mode):
    mock_plan(monkeypatch, query_mode=mode, retrieval_query='Old bifacial topic in Indiana')
    question = 'What is open-circuit voltage?'
    assert decide_rag_source(question, 'key', HISTORY)['retrieval_query'] == question


@pytest.mark.parametrize('fields', [{}, {'query_mode':'bogus','retrieval_query':'bad'},
    {'query_mode':'contextual','retrieval_query':''}, {'query_mode':'contextual','retrieval_query':[]},
    {'query_mode':'contextual','retrieval_query':'a'*1201}])
def test_bad_rewrite_preserves_original_and_research_route(monkeypatch, fields):
    mock_plan(monkeypatch, **fields)
    result=decide_rag_source('What does it mean?', 'key', HISTORY)
    assert result['retrieval_query']=='What does it mean?'
    assert result['source']=='both'
    assert result['query_mode']=='fallback'


@pytest.mark.parametrize('payload',['[]','null','123','"text"','invalid'])
def test_invalid_router_response_does_not_crash(monkeypatch,payload):
    monkeypatch.setattr('llm.rag_source_router.call_llm',lambda *_:payload)
    result=decide_rag_source('Question?', 'key', HISTORY)
    assert result['source']=='none'
    assert result['retrieval_query']=='Question?'


def test_no_history_or_only_current_message_preserves_original(monkeypatch):
    mock_plan(monkeypatch,query_mode='contextual',retrieval_query='invented context')
    for history in (None,[{'role':'user','content':'Question?'}]):
        assert decide_rag_source('Question?','key',history)['retrieval_query']=='Question?'


def test_history_is_bounded_filters_plots_and_does_not_mutate():
    history=[{'role':'assistant','content':'x'*2000} for _ in range(20)]
    history += [{'role':'system','content':'not conversation'}, {'role':'assistant','content':{'plot':'data'}},
                {'role':'user','content':'Current?'}]
    before=copy.deepcopy(history)
    result=recent_text_history(history,'Current?')
    assert len(result)==6 and sum(len(m['content']) for m in result)==6000
    assert history==before


def test_kill_switch_preserves_original_and_skips_expert_call(monkeypatch):
    monkeypatch.setenv('AGPV_CONTEXTUAL_RAG','false')
    mock_plan(monkeypatch,query_mode='contextual',retrieval_query='rewritten')
    assert decide_rag_source('Original?','key',HISTORY)['retrieval_query']=='Original?'
    monkeypatch.setattr('llm.rag_source_router.call_llm',lambda *_:pytest.fail('unexpected call'))
    assert plan_expert_retrieval('Original?','key',HISTORY)['retrieval_query']=='Original?'


def test_expert_timeout_falls_back_to_original(monkeypatch):
    def timeout(*_): raise TimeoutError('offline')
    monkeypatch.setattr('llm.rag_source_router.call_llm',timeout)
    assert plan_expert_retrieval('What does it mean?','key',HISTORY)=={
        'retrieval_query':'What does it mean?','query_mode':'fallback'}


def test_expert_first_turn_skips_rewrite(monkeypatch):
    monkeypatch.setattr('llm.rag_source_router.call_llm',lambda *_:pytest.fail('unexpected call'))
    assert plan_expert_retrieval('Explain yield','key',[])['retrieval_query']=='Explain yield'

"""Live router/retrieval smoke evaluation; writes queries, chunks and optional answers."""
import argparse,json,os,sys,time
from pathlib import Path
parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--repo',type=Path,default=Path(__file__).resolve().parents[1])
parser.add_argument('--output',type=Path,required=True)
args=parser.parse_args();sys.path.insert(0,str(args.repo))
from dotenv import load_dotenv
from llm.rag_source_router import decide_rag_source,plan_expert_retrieval
from llm.general_agpv_answerer import answer_general_agpv_question
from rag.pipeline import retrieve_for_source
load_dotenv(args.repo/'.env')
key=os.getenv('PURDUE_GENAI_KEY')
if not key: raise SystemExit('PURDUE_GENAI_KEY unavailable; live evaluation not run.')
gain=[{'role':'user','content':'What equation defines bifacial gain in energy?'},
      {'role':'assistant','content':'Bifacial energy gain compares bifacial yield with the optimal monofacial reference yield: BG_E = (Y_BF - Y_Mono_opt)/Y_Mono_opt * 100.'}]
voltage=[{'role':'user','content':'Explain the two-level solar cell open-circuit voltage equation.'},
         {'role':'assistant','content':'q V_oc = (E_1 - E_2) [1 - T_D/T_S]. T_D is device temperature and T_S is sun temperature.'}]
cases=[
('denominator',gain,'What does its denominator mean?','contextual',['bifacial'],True),
('temperature',voltage,'How does increasing device temperature affect it?','contextual',['voltage'],True),
('elliptical',gain,'And the numerator?','contextual',['bifacial'],False),
('new_topic',gain,'What equation describes solar declination as a function of day number?','standalone',[],False),
('same_domain_independent',gain,'What is open-circuit voltage?','standalone',[],False),
('self_contained_reference',gain,'What is LCOE and how is it calculated?','standalone',[],False),
('first_turn',[],'What equation defines bifacial gain in energy?','standalone',[],False),
('ambiguous',[{'role':'user','content':'Compare the LCOE equation and the bifacial gain equation.'},
              {'role':'assistant','content':'These are two different equations. Which one would you like to discuss?'}],
 'Explain that equation.','ambiguous',[],False),
]
results=[];args.output.parent.mkdir(parents=True,exist_ok=True)
for name,history,q,mode,terms,answer in cases:
    print('Evaluating',name,flush=True)
    started=time.perf_counter()
    plan=decide_rag_source(q,key,history+[{'role':'user','content':q}])
    elapsed=round(1000*(time.perf_counter()-started))
    actual=plan['retrieval_query']
    passed=plan['query_mode']==mode and (actual==q if mode!='contextual' else all(t in actual.lower() for t in terms))
    original=retrieve_for_source(plan['source'],q)
    contextual=retrieve_for_source(plan['source'],actual)
    row=dict(case_id=name,question=q,history=history,expected_mode=mode,plan=plan,check_passed=passed,
             planning_ms=elapsed,original_chunks=original,contextual_chunks=contextual)
    if answer:
        row['answer']=answer_general_agpv_question(q,key,conversation_history=history+[{'role':'user','content':q}],retrieved_context=contextual)
    results.append(row)
    args.output.write_text(json.dumps(results,indent=2,ensure_ascii=False),encoding='utf-8')
    print(name,plan,'PASS' if passed else 'REVIEW',flush=True)
print('Passed',sum(r['check_passed'] for r in results),'/',len(results),flush=True)

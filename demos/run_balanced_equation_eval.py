"""Run the frozen app's retrieval benchmark, adding joint source/page metrics."""
import argparse, csv, json, sys, statistics, time
from pathlib import Path
parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--repo',type=Path,default=Path(__file__).resolve().parents[1])
parser.add_argument('--cases-dir',type=Path)
parser.add_argument('--output-dir',type=Path)
args=parser.parse_args()
REPO=args.repo.resolve()
sys.path.insert(0,str(REPO))
from demos.compare_equation_rag import evaluate_case
from rag.pipeline import search_collection, search_collection_equation_aware
CASES=args.cases_dir or REPO/'demos'
ROOT=args.output_dir or REPO/'outputs'/'equation_balanced_20261018'
ROOT.mkdir(parents=True,exist_ok=True)
summary={}
for kind in ('paper','book'):
    rows=list(csv.DictReader((CASES/f'{kind}_equation_cases.csv').open(encoding='utf-8-sig')))
    old=f'ceed_group_{kind}s'; new=old+'_equations_v1'
    start=time.perf_counter()
    search_collection(old,'solar irradiance equation',n_results=5)
    search_collection_equation_aware(new,'solar irradiance equation',n_results=5)
    warmup=time.perf_counter()-start
    results=[]
    for row in rows:
        print(kind,row['case_id'],flush=True)
        result=evaluate_case(row,old,new,5)
        result['concept']=row['concept']
        for mode in ('old','new'):
            chunks=json.loads(result[mode+'_chunks'])
            matches=[c for c in chunks if c['title']==row['expected_title_contains'] and str(c['page'])==row['expected_page']]
            result[mode+'_joint_source_page_hit']=bool(matches)
            result[mode+'_first_source_page_rank']=min((c['rank'] for c in matches),default='')
        results.append(result)
    with (ROOT/f'{kind}_balanced_comparison.csv').open('w',encoding='utf-8-sig',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(results[0])); w.writeheader(); w.writerows(results)
    stats={'cases':len(rows),'warmup_seconds':warmup,'sources':len(set(r['expected_title_contains'] for r in rows))}
    for mode in ('old','new'):
        stats[mode]={}
        for key in ('equation_hit_at_k','expected_term_recall','expected_source_hit','expected_page_hit','joint_source_page_hit','retrieval_ms'):
            stats[mode][key]=statistics.mean(float(r[mode+'_'+key]) for r in results)
        stats[mode]['median_retrieval_ms']=statistics.median(r[mode+'_retrieval_ms'] for r in results)
        ranks=[r[mode+'_first_equation_rank'] for r in results if r[mode+'_first_equation_rank']]
        stats[mode]['mean_first_equation_rank_when_found']=statistics.mean(ranks)
        stats[mode]['equation_mrr_at_5']=statistics.mean(1/r[mode+'_first_equation_rank'] if r[mode+'_first_equation_rank'] else 0 for r in results)
    summary[kind]=stats
    print(json.dumps(stats,indent=2),flush=True)
(ROOT/'balanced_summary.json').write_text(json.dumps(summary,indent=2),encoding='utf-8')

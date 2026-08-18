import csv
import os
from pathlib import Path

from dotenv import load_dotenv

from constants import PAPERS_COLLECTION_NAME
from rag.pipeline import answer_from_collection


COLLECTION_NAME = PAPERS_COLLECTION_NAME
PROJECT_ROOT = Path(__file__).resolve().parents[1]
OUTPUT_PATH = PROJECT_ROOT / "outputs" / "rag_answer_demo_results.csv"


RAG_DEMO_CASES = [
    {
        "case_id": "farmer_row_spacing",
        "user_profile": {
            "user_type": "Farmer/Landowner",
            "solar_experience": "Beginner-I am new to solar farm design.",
            "project_goal": "Understand if AgPV is feasible for my land",
        },
        "question": "If I leave more space between solar panel rows, how would that affect the system?",
    },
    {
        "case_id": "farmer_crop_access",
        "user_profile": {
            "user_type": "Farmer/Landowner",
            "solar_experience": "Some experience-I know the basics.",
            "project_goal": "Understand if AgPV is feasible for my land",
        },
        "question": "Why might vertical bifacial panels be useful when I still need access to the land?",
    },
    {
        "case_id": "developer_bifacial_vs_monofacial",
        "user_profile": {
            "user_type": "Solar developer",
            "solar_experience": "Technical-I understand solar farm design terms.",
            "project_goal": "Compare solar farm design options",
        },
        "question": "How do vertical bifacial solar farms compare with tilted monofacial farms?",
    },
    {
        "case_id": "researcher_validation",
        "user_profile": {
            "user_type": "Researcher",
            "solar_experience": "Expert-I have technical experience designing or modeling solar systems",
            "project_goal": "Support research or planning",
        },
        "question": "What experimental or modeling evidence supports the bifacial solar farm conclusions?",
    },
    {
        "case_id": "policymaker_land_use",
        "user_profile": {
            "user_type": "Policymaker",
            "solar_experience": "Beginner-I am new to solar farm design.",
            "project_goal": "Learn about agrivoltaics",
        },
        "question": "Can agrivoltaics help reduce land-use conflicts between farming and solar energy?",
    },
    {
        "case_id": "technical_albedo",
        "user_profile": {
            "user_type": "Researcher",
            "solar_experience": "Technical-I understand solar farm design terms.",
            "project_goal": "Compare solar farm design options",
        },
        "question": "Who will be the next US President?",
    },
    {
        "case_id": "farmer_crop_shading_misconception",
        "user_profile": {
            "user_type": "Farmer/Landowner",
            "solar_experience": "Beginner-I am new to solar farm design.",
            "project_goal": "Understand if AgPV is feasible for my land",
        },
        "question": "Will solar panels shade my crops too much to grow anything?",
    },
    {
        "case_id": "farmer_water_use_claim",
        "user_profile": {
            "user_type": "Farmer/Landowner",
            "solar_experience": "Some experience-I know the basics.",
            "project_goal": "Learn about agrivoltaics",
        },
        "question": "Does having panels over my crops mean I need to water them less?",
    },
    {
        "case_id": "farmer_gsvbf_definition",
        "user_profile": {
            "user_type": "Farmer/Landowner",
            "solar_experience": "Technical-I understand solar farm design terms.",
            "project_goal": "Compare solar farm design options",
        },
        "question": "Is ground-sculpted vertical bifacial (GSVBF) actually different from regular vertical bifacial, or just marketing?",
    },
    {
        "case_id": "developer_tracking_vs_fixed_tilt",
        "user_profile": {
            "user_type": "Solar developer",
            "solar_experience": "Technical-I understand solar farm design terms.",
            "project_goal": "Compare solar farm design options",
        },
        "question": "What's the tradeoff between single-axis tracking and fixed-tilt bifacial in cost and yield?",
    },
    {
        "case_id": "developer_soiling_loss",
        "user_profile": {
            "user_type": "Solar developer",
            "solar_experience": "Expert-I have technical experience designing or modeling solar systems",
            "project_goal": "Estimate solar energy yield",
        },
        "question": "How does soiling loss specifically affect vertical bifacial performance vs. tilted monofacial?",
    },
    {
        "case_id": "developer_latitude_crossover",
        "user_profile": {
            "user_type": "Solar developer",
            "solar_experience": "Expert-I have technical experience designing or modeling solar systems",
            "project_goal": "Compare solar farm design options",
        },
        "question": "At what latitude does tilted monofacial start to outperform vertical bifacial?",
    },
    {
        "case_id": "researcher_ml_prediction",
        "user_profile": {
            "user_type": "Researcher",
            "solar_experience": "Expert-I have technical experience designing or modeling solar systems",
            "project_goal": "Support research or planning",
        },
        "question": "What machine learning approaches have been used to predict solar farm performance at scale?",
    },
    {
        "case_id": "researcher_perovskite_tandem_economics",
        "user_profile": {
            "user_type": "Researcher",
            "solar_experience": "Technical-I understand solar farm design terms.",
            "project_goal": "Compare solar farm design options",
        },
        "question": "How do perovskite-silicon tandem cells change the economics of utility-scale bifacial farms?",
    },
    {
        "case_id": "researcher_experimental_validation",
        "user_profile": {
            "user_type": "Researcher",
            "solar_experience": "Expert-I have technical experience designing or modeling solar systems",
            "project_goal": "Support research or planning",
        },
        "question": "What experimental setups have been used to validate bifacial yield models against real-world data?",
    },
    {
        "case_id": "researcher_beginner_simple_explanation",
        "user_profile": {
            "user_type": "Researcher",
            "solar_experience": "Beginner-I am new to solar farm design.",
            "project_goal": "Learn about agrivoltaics",
        },
        "question": "What's the simplest explanation of why vertical panels can outperform tilted ones?",
    },
    {
        "case_id": "policymaker_adoption_barriers",
        "user_profile": {
            "user_type": "Policymaker",
            "solar_experience": "Beginner-I am new to solar farm design.",
            "project_goal": "Learn about agrivoltaics",
        },
        "question": "What are the main barriers to wider agrivoltaics adoption?",
    },
    {
        "case_id": "policymaker_food_security",
        "user_profile": {
            "user_type": "Policymaker",
            "solar_experience": "Some experience-I know the basics.",
            "project_goal": "Support research or planning",
        },
        "question": "Is there evidence agrivoltaics affects local food security?",
    },
    {
        "case_id": "policymaker_crop_yield_guardrail",
        "user_profile": {
            "user_type": "Policymaker",
            "solar_experience": "Technical-I understand solar farm design terms.",
            "project_goal": "Estimate solar energy yield",
        },
        "question": "What crop yield tradeoffs should I expect if I approve agrivoltaics instead of open-field solar?",
    },
    {
        "case_id": "farmer_cost_savings_guardrail",
        "user_profile": {
            "user_type": "Farmer/Landowner",
            "solar_experience": "Some experience-I know the basics.",
            "project_goal": "Estimate solar energy yield",
        },
        "question": "Can you tell me exactly how much money I'd save switching to vertical bifacial panels?",
    },
]


def summarize_sources(sources):
    source_lines = []

    for source in sources:
        source_lines.append(
            f"{source.get('title')} | page {source.get('page')} | {source.get('headings')}"
        )

    return "\n".join(source_lines)


def run_demo_cases(api_key):
    rows = []

    for demo_case in RAG_DEMO_CASES:
        print(f"Running case: {demo_case['case_id']}")

        response = answer_from_collection(
            collection_name=COLLECTION_NAME,
            question=demo_case["question"],
            api_key=api_key,
            n_results=3,
            user_profile=demo_case["user_profile"],
        )

        rows.append({
            "case_id": demo_case["case_id"],
            "user_type": demo_case["user_profile"]["user_type"],
            "solar_experience": demo_case["user_profile"]["solar_experience"],
            "project_goal": demo_case["user_profile"]["project_goal"],
            "question": demo_case["question"],
            "answer": response["answer"],
            "sources": summarize_sources(response["sources"]),
        })

    return rows


def write_results(rows, output_path):
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with output_path.open("w", newline="", encoding="utf-8") as output_file:
        writer = csv.DictWriter(
            output_file,
            fieldnames=[
                "case_id",
                "user_type",
                "solar_experience",
                "project_goal",
                "question",
                "answer",
                "sources",
            ],
        )
        writer.writeheader()
        writer.writerows(rows)


def main():
    load_dotenv()
    api_key = os.getenv("PURDUE_GENAI_KEY")

    if not api_key:
        raise ValueError("PURDUE_GENAI_KEY is missing from the environment.")

    rows = run_demo_cases(api_key)
    write_results(rows, OUTPUT_PATH)

    print(f"Saved RAG demo results to {OUTPUT_PATH}")


if __name__ == "__main__":
    main()

from fastapi import FastAPI
from app.models.requests import FullPipelineRequest
from app.agents.analyzer import analyze_cv_and_job
from app.agents.comparator import compare_with_country_rules
from app.agents.generator import generate_cv

app = FastAPI()

@app.post("/full-pipeline")
def full_pipeline(data: FullPipelineRequest):

    analysis = analyze_cv_and_job(
        cv_markdown=data.cv_markdown,
        job_offer_markdown=data.job_offer_markdown,
        country=data.country,
        country_rules=data.country_rules
    )

    compliance = compare_with_country_rules(
        analysis=analysis,
        country_rules=data.country_rules,
        cv_markdown=data.cv_markdown
    )

    final_cv = generate_cv(
        analysis=analysis,
        cv_markdown=data.cv_markdown,
        country_rules=data.country_rules
    )

    return {
        "analysis": analysis,
        "country_compliance": compliance,
        "generated_cv": final_cv
    }

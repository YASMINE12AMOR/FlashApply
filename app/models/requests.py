from pydantic import BaseModel

class FullPipelineRequest(BaseModel):
    cv_markdown: str
    job_offer_markdown: str
    country: str
    country_rules: dict

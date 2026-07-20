"""QualityPilot control-plane API."""

from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import Depends, FastAPI, HTTPException, Response
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest
from pydantic import BaseModel
from sqlalchemy.orm import Session

from qualitypilot.ai_quality.deterministic import DeterministicAIQualityAdapter, demo_agent
from qualitypilot.analysis.failure_analyzer import DeterministicFailureAnalyzer
from qualitypilot.database import DefectRecord, TestExecution, get_db, init_db
from qualitypilot.defect_reporting.reporter import (
    build_defect,
    to_jira_payload,
    to_markdown,
    write_reports,
)
from qualitypilot.flaky_detection.detector import FlakyDetector, failure_signature, record_execution
from qualitypilot.generators.deterministic import DeterministicTestGenerator
from qualitypilot.models.analysis import FailureInput
from qualitypilot.observability.middleware import ObservabilityMiddleware
from qualitypilot.requirements.parser import LocalRequirementAdapter


class RequirementInput(BaseModel):
    content: str
    source_format: str


class ExecutionInput(BaseModel):
    test_id: str
    status: str
    duration_seconds: float = 0
    retry_count: int = 0
    error_message: str | None = None
    commit_sha: str = "local"
    environment: str = "local"
    browser: str | None = None
    test_data_version: str = "v1"
    evidence: dict = {}


class DefectInput(BaseModel):
    failure: FailureInput
    related_test_case: str
    commit_sha: str = "local"


class AgentInput(BaseModel):
    prompt: str
    requested_tool: str | None = None
    approved: bool = False


@asynccontextmanager
async def lifespan(_: FastAPI):
    init_db()
    yield


app = FastAPI(title="QualityPilot API", version="0.1.0", lifespan=lifespan)
app.add_middleware(ObservabilityMiddleware, app_name="quality_api")
parser, generator, analyzer, flaky = (
    LocalRequirementAdapter(),
    DeterministicTestGenerator(),
    DeterministicFailureAnalyzer(),
    FlakyDetector(),
)


@app.get("/health")
def health():
    return {"status": "healthy", "service": "qualitypilot-api"}


@app.get("/metrics", include_in_schema=False)
def metrics():
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)


@app.post("/api/requirements/generate")
def generate(payload: RequirementInput):
    try:
        return [
            generator.generate(req) for req in parser.ingest(payload.content, payload.source_format)
        ]
    except (ValueError, TypeError) as exc:
        raise HTTPException(422, str(exc)) from exc


@app.post("/api/failures/analyze")
def analyze_failure(payload: FailureInput):
    return analyzer.analyze(payload)


@app.post("/api/executions", status_code=201)
def add_execution(payload: ExecutionInput, db: Session = Depends(get_db)):
    values = payload.model_dump(exclude={"error_message"})
    values["failure_signature"] = failure_signature(payload.error_message)
    return record_execution(db, **values)


@app.get("/api/executions")
def list_executions(limit: int = 100, db: Session = Depends(get_db)):
    return (
        db.query(TestExecution)
        .order_by(TestExecution.timestamp.desc())
        .limit(min(limit, 500))
        .all()
    )


@app.get("/api/flaky/{test_id}")
def flaky_test(test_id: str, db: Session = Depends(get_db)):
    rows = (
        db.query(TestExecution)
        .filter(TestExecution.test_id == test_id)
        .order_by(TestExecution.timestamp)
        .limit(20)
        .all()
    )
    return flaky.analyze(test_id, rows)


@app.post("/api/defects")
def create_defect(payload: DefectInput, db: Session = Depends(get_db)):
    analysis = analyzer.analyze(payload.failure)
    report = build_defect(payload.failure, analysis, payload.related_test_case, payload.commit_sha)
    paths = write_reports(report, Path("reports/generated"))
    stored = db.query(DefectRecord).filter(DefectRecord.defect_id == report.defect_id).first()
    if stored:
        stored.title = report.title
        stored.report_json = report.model_dump(mode="json")
        stored.markdown_path = paths["markdown"]
    else:
        db.add(
            DefectRecord(
                defect_id=report.defect_id,
                title=report.title,
                report_json=report.model_dump(mode="json"),
                markdown_path=paths["markdown"],
            )
        )
    db.commit()
    return {
        "report": report,
        "markdown": to_markdown(report),
        "jira_payload": to_jira_payload(report),
        "artifacts": paths,
    }


@app.get("/api/defects")
def list_defects(limit: int = 25, db: Session = Depends(get_db)):
    return (
        db.query(DefectRecord).order_by(DefectRecord.created_at.desc()).limit(min(limit, 100)).all()
    )


@app.post("/api/ai/agent")
def agent(payload: AgentInput):
    return demo_agent(payload.prompt, payload.requested_tool, payload.approved)


@app.post("/api/ai/evaluate")
def evaluate(case: dict):
    return DeterministicAIQualityAdapter().evaluate(case)


@app.post("/api/mock-jira", status_code=202)
def mock_jira(payload: dict):
    return {"accepted": True, "external_write": False, "payload": payload}

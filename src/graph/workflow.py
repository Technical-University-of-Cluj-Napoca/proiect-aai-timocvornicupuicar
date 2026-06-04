import os
import sys
import time
import json
from datetime import datetime
from typing import TypedDict, List, Dict, Any
from dotenv import load_dotenv

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from src.dtos import (
    ParsedDocumentDTO,
    RetrievalResultDTO,
    RiskAssessmentDTO,
    RecommendationDTO,
    RiskLevel
)
from src.agents.parser_agent import DocumentParserAgent
from src.agents.retrieval_agent import RAGRetrievalAgent
from src.agents.risk_agent import RiskAssessmentAgent
from src.agents.recommendation_agent import RecommendationAgent

from langgraph.graph import StateGraph, START, END

load_dotenv()


class WorkflowState(TypedDict):
    pdf_path: str
    parsed_doc: ParsedDocumentDTO
    context_map: Dict[str, List[RetrievalResultDTO]]
    risk_map: Dict[str, RiskAssessmentDTO]
    high_risk_alert: bool
    recommendations: List[RecommendationDTO]
    report_path: str
    iteration: int
    timestamp: str


def get_log_file_path(timestamp: str) -> str:
    logs_dir = os.path.abspath("logs")
    os.makedirs(logs_dir, exist_ok=True)
    return os.path.join(logs_dir, f"run_{timestamp}.json")


def append_node_log(timestamp: str, node_name: str, duration: float, tokens_consumed: int):
    log_path = get_log_file_path(timestamp)

    log_entry = {
        "node": node_name,
        "duration_seconds": round(duration, 3),
        "tokens_consumed": tokens_consumed,
        "timestamp": datetime.now().isoformat()
    }

    existing_logs = []

    if os.path.exists(log_path):
        try:
            with open(log_path, "r", encoding="utf-8") as f:
                existing_logs = json.load(f)

            if not isinstance(existing_logs, list):
                existing_logs = []
        except Exception:
            existing_logs = []

    existing_logs.append(log_entry)

    with open(log_path, "w", encoding="utf-8") as f:
        json.dump(existing_logs, f, indent=4, ensure_ascii=False)


def parse_document_node(state: WorkflowState) -> Dict[str, Any]:
    print("\n--- [Node] parse_document ---")
    start_time = time.time()

    timestamp = state.get("timestamp") or datetime.now().strftime("%Y%m%d_%H%M%S")

    parser = DocumentParserAgent()
    parsed_doc = parser.parse(state["pdf_path"])

    duration = time.time() - start_time

    append_node_log(timestamp, "parse_document", duration, tokens_consumed=2000)

    return {
        "parsed_doc": parsed_doc,
        "timestamp": timestamp,
        "iteration": 0
    }


def retrieve_context_node(state: WorkflowState) -> Dict[str, Any]:
    print("\n--- [Node] retrieve_context ---")
    start_time = time.time()

    parsed_doc = state["parsed_doc"]
    iteration = state.get("iteration", 0)

    # La fiecare retry, retrieval-ul devine mai permisiv:
    # iteratia 0: k=5, threshold=0.10
    # iteratia 1: k=8, threshold=0.07
    # iteratia 2: k=11, threshold=0.0
    k = 5 + (iteration * 3)

    if iteration == 0:
        threshold = 0.10
    elif iteration == 1:
        threshold = 0.07
    else:
        threshold = 0.0

    print(
        f"Retrieving context for {len(parsed_doc.clauses)} clauses "
        f"(k={k}, threshold={threshold})..."
    )

    retriever = RAGRetrievalAgent()
    context_map = {}

    for clause in parsed_doc.clauses:
        chunks = retriever.retrieve(clause, k=k, threshold=threshold)
        context_map[clause.id] = chunks

    duration = time.time() - start_time

    append_node_log(
        state["timestamp"],
        f"retrieve_context (iter {iteration})",
        duration,
        tokens_consumed=0
    )

    return {
        "context_map": context_map
    }


def assess_risk_node(state: WorkflowState) -> Dict[str, Any]:
    print("\n--- [Node] assess_risk ---")
    start_time = time.time()

    parsed_doc = state["parsed_doc"]
    context_map = state["context_map"]

    assessor = RiskAssessmentAgent()
    risk_map = {}
    total_tokens = 0

    for clause in parsed_doc.clauses:
        context_chunks = context_map.get(clause.id, [])
        assessment = assessor.assess(clause, context_chunks)
        risk_map[clause.id] = assessment

        if not assessment.context_was_empty:
            total_tokens += 1300

    duration = time.time() - start_time

    append_node_log(
        state["timestamp"],
        "assess_risk",
        duration,
        tokens_consumed=total_tokens
    )

    return {
        "risk_map": risk_map
    }


def increase_iteration_node(state: WorkflowState) -> Dict[str, Any]:
    """
    Nod separat pentru incrementarea iteratiei.
    Important: modificarea state-ului nu trebuie facuta in conditional edge,
    pentru ca LangGraph nu pastreaza sigur acel update.
    """
    print("\n--- [Node] increase_iteration ---")

    old_iteration = state.get("iteration", 0)
    new_iteration = old_iteration + 1

    print(f"Increasing iteration from {old_iteration} to {new_iteration}")

    append_node_log(
        state["timestamp"],
        "increase_iteration",
        duration=0.0,
        tokens_consumed=0
    )

    return {
        "iteration": new_iteration
    }


def flag_high_risk_node(state: WorkflowState) -> Dict[str, Any]:
    print("\n--- [Node] flag_high_risk ---")
    start_time = time.time()

    risk_map = state["risk_map"]

    high_risk_count = sum(
        1 for r in risk_map.values()
        if r.risk_level == RiskLevel.RIDICAT
    )

    high_risk_alert = high_risk_count > 2

    print(f"High risk clauses found: {high_risk_count}. Alert set: {high_risk_alert}")

    duration = time.time() - start_time

    append_node_log(
        state["timestamp"],
        "flag_high_risk",
        duration,
        tokens_consumed=0
    )

    return {
        "high_risk_alert": high_risk_alert
    }


def generate_recommendations_node(state: WorkflowState) -> Dict[str, Any]:
    print("\n--- [Node] generate_recommendations ---")
    start_time = time.time()

    parsed_doc = state["parsed_doc"]
    risk_map = state["risk_map"]
    context_map = state["context_map"]

    recommender = RecommendationAgent()
    recommendations = []
    total_tokens = 0

    for clause in parsed_doc.clauses:
        risk = risk_map.get(clause.id)
        context_chunks = context_map.get(clause.id, [])

        if risk:
            rec = recommender.recommend(clause, risk, context_chunks)
            recommendations.append(rec)

            if risk.risk_level == RiskLevel.MEDIU:
                total_tokens += 1500
            elif risk.risk_level == RiskLevel.RIDICAT:
                total_tokens += 6000

    duration = time.time() - start_time

    append_node_log(
        state["timestamp"],
        "generate_recommendations",
        duration,
        tokens_consumed=total_tokens
    )

    return {
        "recommendations": recommendations
    }


def compile_report_node(state: WorkflowState) -> Dict[str, Any]:
    print("\n--- [Node] compile_report ---")
    start_time = time.time()

    parsed_doc = state["parsed_doc"]
    risk_map = state["risk_map"]
    recommendations = state["recommendations"]

    report_path = (
        state.get("report_path")
        or f"data/contract_audit_report_{state['timestamp']}.md"
    )

    results = []

    for clause in parsed_doc.clauses:
        results.append({
            "clause": clause,
            "risk": risk_map.get(clause.id),
            "rec": next(
                (r for r in recommendations if r.clause_id == clause.id),
                None
            ),
            "metadata": parsed_doc.metadata
        })

    recommender = RecommendationAgent()
    recommender.generate_report(results, report_path)

    duration = time.time() - start_time

    append_node_log(
        state["timestamp"],
        "compile_report",
        duration,
        tokens_consumed=0
    )

    return {
        "report_path": report_path
    }


def quality_check_edge(state: WorkflowState) -> str:
    """
    Decide daca se reia retrieval-ul.
    Daca peste 40% dintre clauze sunt NECUNOSCUT si iteration < 2,
    trimite fluxul catre nodul increase_iteration, apoi inapoi la retrieve_context.
    """
    risk_map = state.get("risk_map", {})
    iteration = state.get("iteration", 0)

    if not risk_map:
        return "proceed"

    unknown_count = sum(
        1 for r in risk_map.values()
        if r.risk_level == RiskLevel.NECUNOSCUT
    )

    total_count = len(risk_map)
    unknown_ratio = unknown_count / total_count if total_count > 0 else 0.0

    print(
        f"[Quality Check] Unknown risk ratio: {unknown_ratio:.1%}, "
        f"Current Iteration: {iteration}"
    )

    if unknown_ratio > 0.40 and iteration < 2:
        print(
            "Quality Check FAILED (>40% unknown risks). "
            "Initiating retry with relaxed RAG parameters..."
        )
        return "retry"

    print("Quality Check PASSED. Continuing to recommendations...")
    return "proceed"


def build_workflow_graph() -> StateGraph:
    workflow = StateGraph(WorkflowState)

    workflow.add_node("parse_document", parse_document_node)
    workflow.add_node("retrieve_context", retrieve_context_node)
    workflow.add_node("assess_risk", assess_risk_node)
    workflow.add_node("increase_iteration", increase_iteration_node)
    workflow.add_node("flag_high_risk", flag_high_risk_node)
    workflow.add_node("generate_recommendations", generate_recommendations_node)
    workflow.add_node("compile_report", compile_report_node)

    workflow.add_edge(START, "parse_document")
    workflow.add_edge("parse_document", "retrieve_context")
    workflow.add_edge("retrieve_context", "assess_risk")

    workflow.add_conditional_edges(
        "assess_risk",
        quality_check_edge,
        {
            "retry": "increase_iteration",
            "proceed": "flag_high_risk"
        }
    )

    workflow.add_edge("increase_iteration", "retrieve_context")
    workflow.add_edge("flag_high_risk", "generate_recommendations")
    workflow.add_edge("generate_recommendations", "compile_report")
    workflow.add_edge("compile_report", END)

    return workflow


def save_graph_diagram(compiled_graph):
    """Saves the visual mermaid rendering of the compiled graph to logs."""
    logs_dir = os.path.abspath("logs")
    os.makedirs(logs_dir, exist_ok=True)

    graph_img_path = os.path.join(logs_dir, "workflow_graph.png")

    try:
        png_data = compiled_graph.get_graph().draw_mermaid_png()

        with open(graph_img_path, "wb") as f:
            f.write(png_data)

        print(f"Workflow graph layout saved to '{graph_img_path}'.")

    except Exception as e:
        print(
            "Could not render and save graph diagram "
            f"(likely missing pygraphviz or connection): {e}"
        )

        with open(os.path.join(logs_dir, "workflow_graph.txt"), "w", encoding="utf-8") as f:
            f.write(
                "START -> parse_document -> retrieve_context -> assess_risk "
                "-> quality_check -> increase_iteration/retry OR flag_high_risk "
                "-> generate_recommendations -> compile_report -> END"
            )


def run_pipeline(pdf_path: str, report_path: str = None) -> Dict[str, Any]:
    """Runs the entire legal analyzer pipeline end-to-end."""
    print(f"Initializing workflow pipeline run for: {pdf_path}")

    workflow_graph = build_workflow_graph()
    app = workflow_graph.compile()

    save_graph_diagram(app)

    inputs = {
        "pdf_path": pdf_path,
        "report_path": report_path,
        "iteration": 0
    }

    result = app.invoke(inputs)

    print("Pipeline run completed successfully!")
    return result


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python src/graph/workflow.py <path_to_pdf>")
        sys.exit(1)

    pdf = sys.argv[1]
    run_pipeline(pdf)
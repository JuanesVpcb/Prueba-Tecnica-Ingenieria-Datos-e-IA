from __future__ import annotations

from typing import Any, TypedDict

from sqlalchemy.orm import Session

from src.ai.tools import execute_read_only_query, query_for_intent, summarize_result

try:
    from langgraph.graph import END, StateGraph
except Exception:  # pragma: no cover
    END = "END"
    StateGraph = None


class AgentState(TypedDict, total=False):
    user_input: str
    intent: str
    sql: str
    rows: list[dict[str, Any]]
    answer_text: str
    answer_json: dict[str, Any]


class InsightAgent:
    def __init__(self) -> None:
        self.graph = self._build_graph()

    def _classify(self, state: AgentState) -> AgentState:
        text: str = state["user_input"].lower()
        if any(token in text for token in ("actualiza", "ingesta", "refresh", "sube", "carga", "update", "refresca", "subir", "cargar",
                                           "actualizar", "ingestar", "refrescar", "subiendo", "cargando")):
            intent: str = "update"
        elif any(token in text for token in ("estrategia", "recomendación", "roi", "cac", "conversion", "retencion", "estadisticas", 
                                             "analisis", "analiza", "analizar", "stats", "metricas", "metrics", "tasa", "rate",
                                             "agrupa", "insight", "sugerencia", "recomienda", "agregada", "por")):
            intent: str = "analysis"
        else:
            intent: str = "data_query"
        return {"intent": intent}

    def _build_sql(self, state: AgentState) -> AgentState:
        if state["intent"] == "update":
            return {"sql": ""}
        return {"sql": query_for_intent(state["intent"], state["user_input"]) }

    def _execute(self, state: AgentState, session: Session) -> AgentState:
        if state["intent"] == "update":
            return {"rows": []}
        return {"rows": execute_read_only_query(session, state["sql"])}

    def _reason(self, state: AgentState) -> AgentState:
        if state["intent"] == "update":
            text: str = "Para actualizar datos, usa el endpoint /data/ingest."
            payload: dict[str, Any] = {"intent": "update", "action": "call_data_ingest"}
            return {"answer_text": text, "answer_json": payload}

        text: str = summarize_result(state["intent"], state.get("rows", []))
        payload: dict[str, Any] = {
            "intent": state["intent"],
            "sql": state.get("sql", ""),
            "rows": state.get("rows", []),
            "summary": text,
        }
        return {"answer_text": text, "answer_json": payload}

    def _build_graph(self):
        if StateGraph is None:
            return None

        graph = StateGraph(AgentState)
        graph.add_node("classify", self._classify)
        graph.add_node("build_sql", self._build_sql)
        graph.add_node("reason", self._reason)

        graph.set_entry_point("classify")
        graph.add_edge("classify", "build_sql")
        graph.add_edge("build_sql", "reason")
        graph.add_edge("reason", END)
        return graph.compile()

    def invoke(self, user_input: str, session: Session) -> dict[str, Any]:
        if self.graph is None:
            state: AgentState = {"user_input": user_input}
            state.update(self._classify(state))
            state.update(self._build_sql(state))
            state.update(self._execute(state, session))
            state.update(self._reason(state))
            return {"text": state["answer_text"], "json": state["answer_json"]}

        state = self.graph.invoke({"user_input": user_input})
        state.update(self._execute(state, session))
        state.update(self._reason(state))
        return {"text": state["answer_text"], "json": state["answer_json"]}

# engine.py
import asyncio
import uuid
from typing import Callable, Dict, Any, List, Optional, Tuple

class Node:
    def __init__(self, name: str, func: Callable[..., Any]):
        self.name = name
        self.func = func  # async or sync callable

class Graph:
    def __init__(self, graph_id: str, nodes: Dict[str, Node], edges: Dict[str, Any], start_node: str):
        self.graph_id = graph_id
        self.nodes = nodes
        self.edges = edges  # mapping node -> next_node or conditional spec
        self.start_node = start_node

class RunState:
    def __init__(self, run_id: str, graph_id: str, initial_state: Dict[str, Any]):
        self.run_id = run_id
        self.graph_id = graph_id
        self.state = initial_state
        self.log: List[str] = []
        self.status = "pending"  # pending, running, finished, failed
        self.current_node: Optional[str] = None
        self._cancel_requested = False

    def add_log(self, msg: str):
        self.log.append(msg)

def eval_condition(cond: Dict[str, Any], state: Dict[str, Any]) -> bool:
    """
    Evaluate a simple JSON-style condition:
      {"key": "quality_score", "op": ">=", "value": 80}
    Supported ops: ==, !=, >, >=, <, <=, in, not-in
    """
    try:
        key = cond.get("key")
        op = cond.get("op", "==")
        val = cond.get("value")
        # support nested keys like metrics.score
        parts = key.split(".") if isinstance(key, str) else []
        cur = state
        for p in parts:
            if isinstance(cur, dict) and p in cur:
                cur = cur[p]
            else:
                cur = None
                break
        left = cur
        if op == "==":
            return left == val
        if op == "!=":
            return left != val
        if op == ">":
            return left > val
        if op == ">=":
            return left >= val
        if op == "<":
            return left < val
        if op == "<=":
            return left <= val
        if op == "in":
            return left in val
        if op == "not-in":
            return left not in val
    except Exception:
        return False
    return False

class GraphEngine:
    def __init__(self):
        self.graphs: Dict[str, Graph] = {}
        self.runs: Dict[str, RunState] = {}
        self.tools: Dict[str, Callable[..., Any]] = {}

    # --- tool registry ---
    def register_tool(self, name: str, func: Callable[..., Any]):
        self.tools[name] = func

    def get_tool(self, name: str):
        return self.tools.get(name)

    # --- graph management ---
    def create_graph(self, nodes_spec: Dict[str, Callable[..., Any]], edges: Dict[str, Any], start_node: str) -> str:
        graph_id = str(uuid.uuid4())
        nodes = {n: Node(n, nodes_spec[n]) for n in nodes_spec}
        graph = Graph(graph_id, nodes, edges, start_node)
        self.graphs[graph_id] = graph
        return graph_id

    # --- run management ---
    def start_run(self, graph_id: str, initial_state: Dict[str, Any]) -> str:
        run_id = str(uuid.uuid4())
        run = RunState(run_id, graph_id, initial_state.copy() if isinstance(initial_state, dict) else {})
        self.runs[run_id] = run
        # start background task
        asyncio.create_task(self._execute_run(run))
        return run_id

    async def _maybe_call(self, func: Callable, state: Dict[str, Any]) -> Any:
        # Node function receives (state, tools) and returns either updated state dict
        # or a tuple (state, next_hint) where next_hint can control branching/looping
        if asyncio.iscoroutinefunction(func):
            res = await func(state, self.tools)
        else:
            loop = asyncio.get_running_loop()
            res = await loop.run_in_executor(None, func, state, self.tools)
        return res

    async def _execute_run(self, run: RunState):
        run.status = "running"
        try:
            graph = self.graphs[run.graph_id]
            current = graph.start_node
            iter_count = 0
            max_iters = 1000  # safety to avoid infinite loops
            while current:
                if run._cancel_requested:
                    run.add_log("cancel requested; stopping")
                    run.status = "failed"
                    return
                iter_count += 1
                if iter_count > max_iters:
                    run.add_log("max iterations exceeded; stopping")
                    run.status = "failed"
                    return

                run.current_node = current
                run.add_log(f"running node: {current}")
                node = graph.nodes[current]
                result = await self._maybe_call(node.func, run.state)

                next_hint = None
                if isinstance(result, tuple) and len(result) == 2:
                    new_state, next_hint = result
                    if isinstance(new_state, dict):
                        run.state.update(new_state)
                elif isinstance(result, dict):
                    run.state.update(result)
                # else allow in-place mutation and None

                run.add_log(f"state after {current}: {run.state}")

                # determine next
                edge = graph.edges.get(current)
                if next_hint:
                    current = next_hint
                elif isinstance(edge, str) or edge is None:
                    current = edge
                elif isinstance(edge, dict):
                    # JSON-based conditional list expected under edge.get("conds", [])
                    conds = edge.get("conds") if isinstance(edge.get("conds"), list) else []
                    chosen = None
                    for c in conds:
                        if c.get("type") == "condition" and eval_condition(c.get("cond", {}), run.state):
                            chosen = c.get("target")
                            break
                    if chosen is None:
                        # fallback to default target if provided
                        for c in conds:
                            if c.get("type") == "default":
                                chosen = c.get("target")
                                break
                    current = chosen
                else:
                    # unknown edge format → finish
                    current = None

            run.status = "finished"
            run.add_log("run finished")
        except Exception as e:
            run.add_log(f"run failed: {e}")
            run.status = "failed"

    def get_run_state(self, run_id: str) -> Optional[RunState]:
        return self.runs.get(run_id)

    def cancel_run(self, run_id: str):
        r = self.runs.get(run_id)
        if r:
            r._cancel_requested = True
            return True
        return False

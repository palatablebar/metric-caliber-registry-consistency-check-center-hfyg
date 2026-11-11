"""Metric dependency graph: Kahn topological sort, Tarjan SCC cycle detection,
orphan detection and layered layout coordinates for the hand-drawn SVG view.

Edge direction convention: ``from_metric`` *requires* ``to_metric``, so a
topological order lists dependencies before the metrics that consume them.
"""
from __future__ import annotations

from typing import Any


def _tarjan_scc(nodes: list[int], adj: dict[int, list[int]]) -> list[list[int]]:
    """Iterative-ish Tarjan (recursive, bounded by the registry size)."""
    index_counter = 0
    stack: list[int] = []
    on_stack: dict[int, bool] = {}
    index: dict[int, int] = {}
    low: dict[int, int] = {}
    result: list[list[int]] = []

    sys_limit = 4000

    def strongconnect(node: int, depth: int = 0) -> None:
        nonlocal index_counter
        if depth > sys_limit:
            return
        index[node] = low[node] = index_counter
        index_counter += 1
        stack.append(node)
        on_stack[node] = True
        for nxt in adj.get(node, []):
            if nxt not in index:
                strongconnect(nxt, depth + 1)
                low[node] = min(low[node], low[nxt])
            elif on_stack.get(nxt):
                low[node] = min(low[node], index[nxt])
        if low[node] == index[node]:
            component: list[int] = []
            while True:
                current = stack.pop()
                on_stack[current] = False
                component.append(current)
                if current == node:
                    break
            result.append(component)

    for node in nodes:
        if node not in index:
            strongconnect(node)
    return result


def _cycle_path(component: list[int], adj: dict[int, list[int]]) -> list[int]:
    members = set(component)
    starts = sorted(component)
    for start in starts:
        path = [start]
        visited = {start}

        def dfs(node: int) -> list[int] | None:
            for nxt in adj.get(node, []):
                if nxt not in members:
                    continue
                if nxt == start:
                    return path + [start]
                if nxt in visited:
                    continue
                visited.add(nxt)
                path.append(nxt)
                found = dfs(nxt)
                if found:
                    return found
                path.pop()
                visited.discard(nxt)
            return None

        found = dfs(start)
        if found:
            return found
    return component + [component[0]]


def build_graph(metrics: list[dict[str, Any]], edges: list[dict[str, Any]]) -> dict[str, Any]:
    """``metrics``: {id, key, name, domain, status, consumers}; ``edges``:
    {from_id, to_id, relation, note} with metric-to-metric edges only."""
    by_id = {metric["id"]: metric for metric in metrics}
    node_ids = sorted(by_id)
    requires: dict[int, list[int]] = {node: [] for node in node_ids}
    dependents: dict[int, list[int]] = {node: [] for node in node_ids}

    edge_rows: list[dict[str, Any]] = []
    for edge in edges:
        source = edge.get("from_id")
        target = edge.get("to_id")
        if source not in by_id or target not in by_id or source == target and False:
            continue
        if source not in by_id or target not in by_id:
            continue
        requires[source].append(target)
        dependents[target].append(source)
        edge_rows.append(
            {
                "from_id": source,
                "to_id": target,
                "from_key": by_id[source]["key"],
                "to_key": by_id[target]["key"],
                "relation": edge.get("relation") or "derive",
                "note": edge.get("note"),
            }
        )

    # ---- Kahn topological sort: dependencies first
    indegree = {node: len(requires[node]) for node in node_ids}
    ready = sorted((node for node in node_ids if indegree[node] == 0), key=lambda n: by_id[n]["key"])
    order: list[int] = []
    while ready:
        node = ready.pop(0)
        order.append(node)
        for consumer in sorted(dependents[node], key=lambda n: by_id[n]["key"]):
            indegree[consumer] -= 1
            if indegree[consumer] == 0:
                ready.append(consumer)
        ready.sort(key=lambda n: by_id[n]["key"])
    cyclic_nodes = [node for node in node_ids if indegree[node] > 0]
    cyclic_set = set(cyclic_nodes)

    # ---- Tarjan SCC -> cycle paths
    components = _tarjan_scc(node_ids, requires)
    cycles: list[dict[str, Any]] = []
    scc_of: dict[int, int] = {}
    for index, component in enumerate(components):
        for node in component:
            scc_of[node] = index
        is_cycle = len(component) > 1 or (len(component) == 1 and component[0] in requires.get(component[0], []))
        if not is_cycle:
            continue
        path = _cycle_path(component, requires)
        cycles.append(
            {
                "members": sorted(component),
                "member_keys": [by_id[node]["key"] for node in sorted(component)],
                "path": path,
                "path_keys": [by_id[node]["key"] for node in path],
                "size": len(component),
            }
        )
    cycles.sort(key=lambda cycle: cycle["member_keys"])
    for edge in edge_rows:
        edge["in_cycle"] = scc_of.get(edge["from_id"]) == scc_of.get(edge["to_id"]) and edge["from_id"] in cyclic_set

    # ---- orphans: nothing depends on it and no BI consumer registered
    orphans = [
        node
        for node in node_ids
        if not dependents[node] and not (by_id[node].get("consumers") or [])
    ]

    # ---- layered layout (dependencies on the left)
    layer: dict[int, int] = {}
    for node in order:
        deps = [dep for dep in requires[node] if dep in layer]
        layer[node] = max((layer[dep] + 1 for dep in deps), default=0)
    for _ in range(len(node_ids) + 2):
        changed = False
        for node in cyclic_nodes:
            deps = [dep for dep in requires[node] if dep not in cyclic_set and dep in layer]
            candidate = max((layer[dep] + 1 for dep in deps), default=0)
            if layer.get(node, -1) < candidate:
                layer[node] = candidate
                changed = True
        if not changed:
            break
    fallback = max(layer.values(), default=-1) + 1
    for node in cyclic_nodes:
        layer.setdefault(node, fallback)

    nodes_out = [
        {
            **{field: by_id[node].get(field) for field in ("id", "key", "name", "domain", "status")},
            "consumers": by_id[node].get("consumers") or [],
            "layer": layer.get(node, 0),
            "in_cycle": node in cyclic_set,
            "is_orphan": node in orphans,
            "dependency_count": len(requires[node]),
            "dependent_count": len(dependents[node]),
        }
        for node in node_ids
    ]

    return {
        "nodes": nodes_out,
        "edges": edge_rows,
        "cycles": cycles,
        "orphans": [by_id[node]["key"] for node in orphans],
        "orphan_nodes": [
            {"id": node, "key": by_id[node]["key"], "name": by_id[node]["name"]} for node in orphans
        ],
        "topological_order": [by_id[node]["key"] for node in order],
        "unresolved_cycle_keys": [by_id[node]["key"] for node in cyclic_nodes],
        "layers": {by_id[node]["key"]: layer.get(node, 0) for node in node_ids},
        "stats": {
            "node_count": len(node_ids),
            "edge_count": len(edge_rows),
            "cycle_count": len(cycles),
            "orphan_count": len(orphans),
            "max_layer": max(layer.values(), default=0),
            "cyclic_metric_count": len(cyclic_nodes),
        },
    }


def impact_closure(
    metric_id: int,
    metrics: list[dict[str, Any]],
    edges: list[dict[str, Any]],
) -> dict[str, Any]:
    """All metrics that transitively *require* ``metric_id`` (downstream consumers),
    plus the BI dashboards registered against them."""
    by_id = {metric["id"]: metric for metric in metrics}
    dependents: dict[int, list[int]] = {node: [] for node in by_id}
    for edge in edges:
        source, target = edge.get("from_id"), edge.get("to_id")
        if source in by_id and target in by_id:
            dependents[target].append(source)

    seen: set[int] = set()
    queue = [metric_id]
    while queue:
        current = queue.pop(0)
        for consumer in sorted(dependents.get(current, [])):
            if consumer not in seen and consumer != metric_id:
                seen.add(consumer)
                queue.append(consumer)

    boards: list[str] = []
    affected: list[dict[str, Any]] = []
    for board in by_id.get(metric_id, {}).get("consumers") or []:
        if board not in boards:
            boards.append(board)
    for node in sorted(seen, key=lambda n: by_id[n]["key"]):
        metric = by_id[node]
        affected.append(
            {"id": node, "key": metric["key"], "name": metric["name"], "domain": metric["domain"]}
        )
        for board in metric.get("consumers") or []:
            if board not in boards:
                boards.append(board)

    return {
        "metric_id": metric_id,
        "metric_key": by_id.get(metric_id, {}).get("key"),
        "affected_metric_count": len(affected),
        "affected_metrics": affected,
        "boards": boards,
        "board_count": len(boards),
    }

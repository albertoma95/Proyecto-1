import heapq
import itertools
from datetime import datetime, timedelta

def dijkstra(graph, start, end):
    queue = [(0, start, [])]
    visited = set()
    while queue:
        (cost, node, path) = heapq.heappop(queue)
        if node == end:
            return cost, path + [end]
        if node in visited:
            continue
        visited.add(node)
        for neighbor, weight in graph.get(node, {}).items():
            if neighbor not in visited:
                heapq.heappush(queue, (cost + weight, neighbor, path + [node]))
    return float('inf'), []

def precompute_distances(graph, nodes):
    dist_matrix = {}
    for from_node in nodes:
        dist_matrix[from_node] = {}
        for to_node in nodes:
            if from_node == to_node:
                dist_matrix[from_node][to_node] = 0
            else:
                distance, _ = dijkstra(graph, from_node, to_node)
                dist_matrix[from_node][to_node] = distance
    return dist_matrix

def calculate_optimal_route(graph, origin, destinations):
    # Resolución simplificada tipo TSP
    all_locations = [origin] + destinations
    n = len(all_locations)
    index = {all_locations[i]: i for i in range(n)}
    dist_matrix = precompute_distances(graph, all_locations)

    C = {}
    for k in range(1, n):
        C[(frozenset([k]), k)] = (dist_matrix[origin][all_locations[k]], origin)

    import itertools
    for s in range(2, n):
        for subset in itertools.combinations(range(1, n), s):
            set_subset = frozenset(subset)
            for k in subset:
                prev_subset = set_subset - {k}
                min_cost = float('inf')
                min_prev = None
                for m in prev_subset:
                    cost = C[(prev_subset, m)][0] + dist_matrix[all_locations[m]][all_locations[k]]
                    if cost < min_cost:
                        min_cost = cost
                        min_prev = m
                C[(set_subset, k)] = (min_cost, min_prev)

    full_set = frozenset(range(1, n))
    min_cost = float('inf')
    last_node = None
    for k in range(1, n):
        cost = C[(full_set, k)][0]
        if cost < min_cost:
            min_cost = cost
            last_node = k

    path = []
    set_subset = full_set
    k = last_node
    while set_subset:
        path.append(all_locations[k])
        prev_k = C[(set_subset, k)][1]
        set_subset = set_subset - {k}
        k = prev_k if isinstance(prev_k, int) else index[prev_k]
    path.append(origin)
    path.reverse()

    return min_cost, path

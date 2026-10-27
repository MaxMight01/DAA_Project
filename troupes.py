"""
Optimal military troupe stationing on a tree (DAA Project, Question 12).

The towns and roads of country XYZ form a tree on n towns. Each town is assigned
0, 1, or 2 troupes, subject to the condition that every town assigned 0 troupes
has at least one neighbour assigned 2 troupes. The objective is to minimise the
total number of troupes.

This module contains:

    min_troupes            the O(n) rooted-tree dynamic program (iterative DFS);
    min_troupes_assignment the same program, extended to reconstruct an optimal
                           assignment f : V -> {0, 1, 2};
    is_feasible            a test of the stationing condition for a given f;
    brute_force_min        an exhaustive O(3^n) reference solver;
    random_tree_prufer,
    random_tree_dsu,
    random_tree_modset     three random-tree generators;
    all_labeled_trees      an exact enumerator of every labelled tree;
    verify                 a suite that checks the program against brute force.

Trees are stored as 1-indexed adjacency lists: adj has length n + 1, entry 0 is
unused, and the towns are 1, ..., n. Run "python troupes.py --help" for the
command-line interface.
"""

from __future__ import annotations

import argparse
from heapq import heapify, heappop, heappush
from itertools import product
from random import choice, randint, seed as set_seed

INF = float("inf")


# --------------------------------------------------------------------------- #
#  The dynamic program                                                        #
# --------------------------------------------------------------------------- #
def min_troupes(adj, n=None, root=1):
    """Return the minimum total number of troupes for the tree adj.

    The traversal is an explicit-stack post-order DFS, so the running time and
    space are both O(n) and the routine handles a path of a million towns, on
    which a recursive DFS would exceed Python's recursion limit.
    """
    if n is None:
        n = len(adj) - 1
    if n == 0:
        return 0

    opt = [0] * (n + 1)    # OPT(v): v internally satisfied, f(v) unrestricted
    dc = [0] * (n + 1)     # DC(v): every town of T_v except possibly v satisfied
    with1 = [0] * (n + 1)  # f(v) = 1, with v and all of T_v satisfied
    with2 = [0] * (n + 1)  # f(v) = 2, with v and all of T_v satisfied

    # Iterative post-order DFS; each frame is (vertex, parent, visited?).
    stack = [(root, 0, False)]
    while stack:
        v, p, visited = stack.pop()
        if not visited:
            stack.append((v, p, True))
            for u in adj[v]:
                if u != p:
                    stack.append((u, v, False))
            continue

        sum_opt = 0           # sum of OPT(u) over the children u of v
        with2[v] = 2
        for u in adj[v]:
            if u == p:
                continue
            sum_opt += opt[u]
            with2[v] += dc[u]          # a 2-town covers its children: charge DC
        with1[v] = sum_opt + 1         # a 1-town covers no child: charge OPT

        # with0(v): f(v) = 0 forces some child w to carry 2 so that v is covered.
        with0 = INF
        for u in adj[v]:
            if u == p:
                continue
            with0 = min(with0, sum_opt - opt[u] + with2[u])

        opt[v] = min(with1[v], with2[v], with0)
        dc[v] = min(opt[v], sum_opt)   # DC also permits f(v) = 0 leaning on p

    return opt[root]


# Decision tags recorded for the reconstruction pass.
_ONE, _TWO, _ZERO = 0, 1, 2          # how OPT(v) was attained
_DC_OPT, _DC_DEFER = 0, 1            # how DC(v) was attained
_M_OPT, _M_DC, _M_TWO = 0, 1, 2      # modes of the top-down pass


def min_troupes_assignment(adj, n=None, root=1):
    """Return (cost, f), where f is an optimal assignment.

    f is a list of length n + 1 with f[v] in {0, 1, 2} the number of troupes at
    town v (f[0] is unused), and sum(f) equals cost equals min_troupes(adj).
    """
    if n is None:
        n = len(adj) - 1
    if n == 0:
        return 0, [0]

    opt = [0] * (n + 1)
    dc = [0] * (n + 1)
    with2 = [0] * (n + 1)
    opt_choice = [0] * (n + 1)   # _ONE / _TWO / _ZERO
    zero_child = [0] * (n + 1)   # for _ZERO: the child designated to carry 2
    dc_choice = [0] * (n + 1)    # _DC_OPT / _DC_DEFER

    stack = [(root, 0, False)]
    while stack:
        v, p, visited = stack.pop()
        if not visited:
            stack.append((v, p, True))
            for u in adj[v]:
                if u != p:
                    stack.append((u, v, False))
            continue

        sum_opt = 0
        w2 = 2
        for u in adj[v]:
            if u == p:
                continue
            sum_opt += opt[u]
            w2 += dc[u]
        with2[v] = w2
        with1 = sum_opt + 1

        with0, w_star = INF, 0
        for u in adj[v]:
            if u == p:
                continue
            cand = sum_opt - opt[u] + with2[u]
            if cand < with0:
                with0, w_star = cand, u

        best = min(with1, with2[v], with0)
        opt[v] = best
        if best == with2[v]:
            opt_choice[v] = _TWO
        elif best == with1:
            opt_choice[v] = _ONE
        else:
            opt_choice[v] = _ZERO
            zero_child[v] = w_star

        if opt[v] <= sum_opt:
            dc[v] = opt[v]
            dc_choice[v] = _DC_OPT
        else:
            dc[v] = sum_opt
            dc_choice[v] = _DC_DEFER

    # Top-down pass: descend from the root, carrying a mode into each vertex.
    f = [0] * (n + 1)
    stack = [(root, 0, _M_OPT)]
    while stack:
        v, p, mode = stack.pop()
        children = [u for u in adj[v] if u != p]

        if mode == _M_DC and dc_choice[v] == _DC_DEFER:
            f[v] = 0
            for u in children:
                stack.append((u, v, _M_OPT))
            continue
        if mode == _M_TWO:
            f[v] = 2
            for u in children:
                stack.append((u, v, _M_DC))
            continue

        # Mode is OPT, or DC resolving to OPT(v): follow opt_choice[v].
        if opt_choice[v] == _ONE:
            f[v] = 1
            for u in children:
                stack.append((u, v, _M_OPT))
        elif opt_choice[v] == _TWO:
            f[v] = 2
            for u in children:
                stack.append((u, v, _M_DC))
        else:  # _ZERO
            f[v] = 0
            w = zero_child[v]
            for u in children:
                stack.append((u, v, _M_TWO if u == w else _M_OPT))

    return opt[root], f


# --------------------------------------------------------------------------- #
#  Feasibility and the brute-force reference solver                           #
# --------------------------------------------------------------------------- #
def is_feasible(adj, f, n=None):
    """Return True if every 0-town in f has a neighbour carrying 2 troupes."""
    if n is None:
        n = len(adj) - 1
    for v in range(1, n + 1):
        if f[v] == 0 and not any(f[u] == 2 for u in adj[v]):
            return False
    return True


def brute_force_min(adj, n=None):
    """Return the minimum by exhaustive search over all 3^n assignments.

    Used only to check the dynamic program on small instances.
    """
    if n is None:
        n = len(adj) - 1
    if n == 0:
        return 0
    best = INF
    f = [0] * (n + 1)
    for combo in product((0, 1, 2), repeat=n):
        for v in range(1, n + 1):
            f[v] = combo[v - 1]
        if is_feasible(adj, f, n):
            best = min(best, sum(combo))
    return best


# --------------------------------------------------------------------------- #
#  Random tree generators (three independent sampling schemes)                #
# --------------------------------------------------------------------------- #
def random_tree_prufer(n):
    """Return a uniformly random labelled tree, drawn via a random Prufer
    sequence. By Cayley's formula the sequences of length n - 2 are in bijection
    with the labelled trees on n vertices, so this sampler is uniform. Decoding
    costs O(n log n) using a heap over the current degrees.
    """
    if n == 1:
        return [[], []]
    if n == 2:
        return [[], [2], [1]]
    seq = [randint(1, n) for _ in range(n - 2)]
    degree = [1] * (n + 1)
    for x in seq:
        degree[x] += 1
    adj = [[] for _ in range(n + 1)]
    leaves = [v for v in range(1, n + 1) if degree[v] == 1]
    heapify(leaves)
    for x in seq:
        leaf = heappop(leaves)
        adj[leaf].append(x)
        adj[x].append(leaf)
        degree[x] -= 1
        if degree[x] == 1:
            heappush(leaves, x)
    u, w = heappop(leaves), heappop(leaves)
    adj[u].append(w)
    adj[w].append(u)
    return adj


def random_tree_dsu(n):
    """Return a random spanning tree grown by accepting random edges.

    Random pairs are drawn and an edge is kept whenever its endpoints lie in
    different components, tested by a disjoint-set-union structure with path
    compression and union by rank, until n - 1 edges have been added.
    """
    parent = list(range(n + 1))
    rank = [0] * (n + 1)
    adj = [[] for _ in range(n + 1)]

    def find(p):
        root = p
        while parent[root] != root:
            root = parent[root]
        while parent[p] != root:
            parent[p], p = root, parent[p]
        return root

    edges = 0
    while edges != n - 1:
        a, b = randint(1, n), randint(1, n)
        ra, rb = find(a), find(b)
        if ra == rb:
            continue
        if rank[ra] < rank[rb]:
            ra, rb = rb, ra
        parent[rb] = ra
        if rank[ra] == rank[rb]:
            rank[ra] += 1
        adj[a].append(b)
        adj[b].append(a)
        edges += 1
    return adj


def random_tree_modset(n):
    """Return a random tree grown in O(n) by repeatedly joining a random
    remaining town to a random town already in the tree.

    The remaining towns are kept in a list together with their positions, so a
    chosen town is removed in O(1) by swapping it to the end before discarding.
    """
    adj = [[] for _ in range(n + 1)]
    added = [1]
    rem = list(range(2, n + 1))
    pos = [0] * (n + 1)              # pos[x] is the index of town x within rem
    for i, x in enumerate(rem):
        pos[x] = i
    for last in range(len(rem) - 1, -1, -1):
        u = choice(added)
        v = choice(rem)
        moved = rem[last]           # town currently at the tail
        rem[pos[v]], rem[last] = moved, v
        pos[moved] = pos[v]
        rem.pop()
        added.append(v)
        adj[u].append(v)
        adj[v].append(u)
    return adj


def all_labeled_trees(n):
    """Yield every labelled tree on n towns exactly once (the Prufer bijection)."""
    if n == 1:
        yield [[], []]
        return
    if n == 2:
        yield [[], [2], [1]]
        return
    for seq in product(range(1, n + 1), repeat=n - 2):
        degree = [1] * (n + 1)
        for x in seq:
            degree[x] += 1
        adj = [[] for _ in range(n + 1)]
        leaves = [v for v in range(1, n + 1) if degree[v] == 1]
        heapify(leaves)
        for x in seq:
            leaf = heappop(leaves)
            adj[leaf].append(x)
            adj[x].append(leaf)
            degree[x] -= 1
            if degree[x] == 1:
                heappush(leaves, x)
        u, w = heappop(leaves), heappop(leaves)
        adj[u].append(w)
        adj[w].append(u)
        yield adj


# --------------------------------------------------------------------------- #
#  Verification suite                                                         #
# --------------------------------------------------------------------------- #
def _check(adj, n):
    """Check the program against brute force and validate its assignment."""
    expected = brute_force_min(adj, n)
    got = min_troupes(adj, n)
    assert got == expected, f"count mismatch: dp={got} brute={expected} on {adj}"
    cost, f = min_troupes_assignment(adj, n)
    assert cost == expected, f"assignment cost {cost} is not the optimum {expected}"
    assert sum(f) == cost, "reported cost does not match the assignment"
    assert is_feasible(adj, f, n), f"reconstructed assignment is infeasible: {f}"


def verify(exhaustive_upto=6, random_upto=10, trials=120, rng_seed=12345):
    """Run the verification suite and return the number of instances checked."""
    set_seed(rng_seed)
    total = 0

    print("Exhaustive over all labelled trees:")
    for n in range(1, exhaustive_upto + 1):
        count = 0
        for adj in all_labeled_trees(n):
            _check(adj, n)
            count += 1
        total += count
        print(f"  n = {n:2d}:  {count:6d} trees  OK")

    print(f"Random trees ({trials} per generator per size):")
    gens = (random_tree_prufer, random_tree_dsu, random_tree_modset)
    for n in range(exhaustive_upto + 1, random_upto + 1):
        for _ in range(trials):
            for gen in gens:
                _check(gen(n), n)
                total += 1
        print(f"  n = {n:2d}:  {trials * len(gens):6d} trees  OK")

    print(f"\n{total} instances checked. In every case the dynamic program "
          "returned the\noptimum, and each reconstructed assignment was "
          "feasible and of optimal cost.")
    return total


def empirical_ratio(n=10_000, trials=1000, generator=random_tree_prufer,
                    rng_seed=0):
    """Return the average of OPT / n over random trees on n towns."""
    set_seed(rng_seed)
    acc = 0.0
    for _ in range(trials):
        acc += min_troupes(generator(n), n) / n
    return acc / trials


# --------------------------------------------------------------------------- #
#  Command-line interface                                                     #
# --------------------------------------------------------------------------- #
def _demo():
    examples = {
        "path on 5 towns": [[], [2], [1, 3], [2, 4], [3, 5], [4]],
        "star on 5 towns": [[], [2, 3, 4, 5], [1], [1], [1], [1]],
    }
    for name, adj in examples.items():
        cost, f = min_troupes_assignment(adj)
        print(f"{name}: minimum = {cost}, assignment = {f[1:]}")


def main():
    parser = argparse.ArgumentParser(
        description="Minimum troupe stationing on a tree.")
    parser.add_argument("--verify", action="store_true",
                        help="run the brute-force verification suite")
    parser.add_argument("--demo", action="store_true",
                        help="print optimal assignments for two sample trees")
    parser.add_argument("--ratio", type=int, metavar="N", default=0,
                        help="report the average OPT/N over random N-town trees")
    parser.add_argument("--trials", type=int, default=1000,
                        help="number of trials for --ratio (default 1000)")
    args = parser.parse_args()

    if args.verify:
        verify()
    if args.ratio:
        r = empirical_ratio(n=args.ratio, trials=args.trials)
        print(f"average OPT/n over {args.trials} random trees on "
              f"n = {args.ratio}: {r:.4f}")
    if args.demo or not (args.verify or args.ratio):
        _demo()


if __name__ == "__main__":
    main()

"""
Correctness tests for B-tree, B+-tree, B*-tree.

Each test verifies structural invariants after every operation:
  - All keys in a node are sorted
  - Non-root nodes have d <= |keys| <= 2d
  - Root has 1 <= |keys| <= 2d  (or 0 keys only when tree is empty)
  - All leaves are at the same depth
  - Internal node children count == keys count + 1
  - Internal node keys correctly separate child key ranges
  - B+-tree: leaf linked list is consistent and sorted
"""

import random
import sys
import traceback
from btree import BT
from bplustree import BPT
from bstartree import BST

PASS = 0
FAIL = 0


def ok(name):
    global PASS
    PASS += 1
    print(f"  PASS  {name}")


def fail(name, msg):
    global FAIL
    FAIL += 1
    print(f"  FAIL  {name}")
    print(f"        {msg}")


# ---------------------------------------------------------------------------
# Invariant checkers
# ---------------------------------------------------------------------------

def check_btree(tree, name=""):
    """Return list of violation strings (empty = valid)."""
    d = tree.order
    violations = []

    def check_node(node, min_key, max_key, depth, is_root):
        # Key count
        n = len(node.keys)
        if is_root:
            if not node.is_leaf and n < 1:
                violations.append(f"{name} root internal node has {n} keys (need >=1)")
        else:
            if n < d:
                violations.append(f"{name} node has {n} keys < d={d}: keys={node.keys}")
            if n > 2 * d:
                violations.append(f"{name} node has {n} keys > 2d={2*d}")

        # record_ids count must match keys
        if len(node.record_ids) != n:
            violations.append(f"{name} node keys={n} but record_ids={len(node.record_ids)}")

        # Keys sorted
        for i in range(n - 1):
            if node.keys[i] >= node.keys[i + 1]:
                violations.append(f"{name} keys not sorted: {node.keys}")
                break

        # Key range
        for k in node.keys:
            if min_key is not None and k <= min_key:
                violations.append(f"{name} key {k} <= min_bound {min_key}")
            if max_key is not None and k >= max_key:
                violations.append(f"{name} key {k} >= max_bound {max_key}")

        if node.is_leaf:
            if node.children:
                violations.append(f"{name} leaf has children")
            return depth

        # Children count
        if len(node.children) != n + 1:
            violations.append(
                f"{name} internal node: {n} keys but {len(node.children)} children"
            )

        leaf_depths = []
        for i, child in enumerate(node.children):
            lo = node.keys[i - 1] if i > 0 else min_key
            hi = node.keys[i] if i < n else max_key
            leaf_depths.append(check_node(child, lo, hi, depth + 1, False))

        # All leaves at same depth
        valid = [d for d in leaf_depths if d is not None]
        if valid and len(set(valid)) > 1:
            violations.append(f"{name} leaves at different depths: {set(valid)}")
        return valid[0] if valid else depth

    check_node(tree.root, None, None, 0, True)
    return violations


def check_bplustree(tree, name=""):
    """BPT-specific: also checks leaf linked list."""
    d = tree.order
    violations = []

    def check_node(node, min_key, max_key, depth, is_root):
        n = len(node.keys)
        if is_root:
            if not node.is_leaf and n < 1:
                violations.append(f"{name} root has {n} keys")
        else:
            if n < d:
                violations.append(f"{name} node has {n} keys < d={d}: keys={node.keys}")
            if n > 2 * d:
                violations.append(f"{name} node has {n} keys > 2d={2*d}")

        # Keys sorted
        for i in range(n - 1):
            if node.keys[i] >= node.keys[i + 1]:
                violations.append(f"{name} keys not sorted: {node.keys}")
                break

        if node.is_leaf:
            if len(node.record_ids) != n:
                violations.append(f"{name} leaf keys={n} record_ids={len(node.record_ids)}")
            if node.children:
                violations.append(f"{name} leaf has children")
            # Key range
            for k in node.keys:
                if min_key is not None and k < min_key:
                    violations.append(f"{name} leaf key {k} < min_bound {min_key}")
                if max_key is not None and k >= max_key:
                    violations.append(f"{name} leaf key {k} >= max_bound {max_key}")
            return depth

        if node.record_ids:
            violations.append(f"{name} internal node has record_ids")
        if len(node.children) != n + 1:
            violations.append(
                f"{name} internal: {n} keys, {len(node.children)} children"
            )

        # Internal key range
        for k in node.keys:
            if min_key is not None and k < min_key:
                violations.append(f"{name} internal key {k} < min_bound {min_key}")
            if max_key is not None and k > max_key:
                violations.append(f"{name} internal key {k} > max_bound {max_key}")

        leaf_depths = []
        for i, child in enumerate(node.children):
            lo = node.keys[i - 1] if i > 0 else min_key
            hi = node.keys[i] if i < n else max_key
            leaf_depths.append(check_node(child, lo, hi, depth + 1, False))

        valid = [x for x in leaf_depths if x is not None]
        if valid and len(set(valid)) > 1:
            violations.append(f"{name} leaves at different depths: {set(valid)}")
        return valid[0] if valid else depth

    check_node(tree.root, None, None, 0, True)

    # Check leaf linked list
    node = tree.root
    while not node.is_leaf:
        node = node.children[0]

    prev_key = None
    while node is not None:
        for k in node.keys:
            if prev_key is not None and k <= prev_key:
                violations.append(f"{name} leaf list not sorted: {prev_key} then {k}")
            prev_key = k
        node = node.next

    return violations


def assert_invariants_bt(tree, label):
    v = check_btree(tree, label)
    if v:
        fail(label, "\n        ".join(v))
    return v


def assert_invariants_bpt(tree, label):
    v = check_bplustree(tree, label)
    if v:
        fail(label, "\n        ".join(v))
    return v


def assert_invariants_bst(tree, label):
    # BST has same structure as BT
    v = check_btree(tree, label)
    if v:
        fail(label, "\n        ".join(v))
    return v


# ---------------------------------------------------------------------------
# Helper: insert a list and verify all can be found
# ---------------------------------------------------------------------------

def insert_all(tree, pairs):
    for k, v in pairs:
        tree.insert(k, v)


def search_all(tree, pairs):
    errors = []
    for k, v in pairs:
        result = tree.search(k)
        if result != v:
            errors.append(f"search({k}): expected {v}, got {result}")
    return errors


def delete_all(tree, keys):
    errors = []
    for k in keys:
        result = tree.delete(k)
        if not result:
            errors.append(f"delete({k}) returned False (key not found)")
    return errors


# ---------------------------------------------------------------------------
# Test cases
# ---------------------------------------------------------------------------

def run_test(name, fn):
    try:
        fn()
    except Exception as e:
        fail(name, f"Exception: {e}\n        " + traceback.format_exc().replace("\n", "\n        "))


# --- 1. Empty tree search ---
def test_empty_search():
    name = "empty tree search"
    for TreeCls in (BT, BPT, BST):
        t = TreeCls(3)
        r = t.search(42)
        if r is not None:
            fail(f"{name} [{TreeCls.__name__}]", f"expected None, got {r}")
            return
    ok(name)

# --- 2. Single insert/search ---
def test_single():
    name = "single insert + search"
    for TreeCls in (BT, BPT, BST):
        t = TreeCls(3)
        t.insert(10, 99)
        r = t.search(10)
        if r != 99:
            fail(f"{name} [{TreeCls.__name__}]", f"expected 99, got {r}")
            return
        v = check_btree(t, TreeCls.__name__) if TreeCls != BPT else check_bplustree(t, TreeCls.__name__)
        if v:
            fail(f"{name} [{TreeCls.__name__}]", str(v))
            return
    ok(name)

# --- 3. Duplicate insert updates value ---
def test_duplicate_insert():
    name = "duplicate insert updates value"
    for TreeCls in (BT, BPT, BST):
        t = TreeCls(3)
        t.insert(5, 1)
        t.insert(5, 2)
        r = t.search(5)
        if r != 2:
            fail(f"{name} [{TreeCls.__name__}]", f"expected 2, got {r}")
            return
    ok(name)

# --- 4. Sequential insert, invariants ---
def test_sequential_insert():
    name = "sequential insert invariants (d=3,5,10)"
    for d in (3, 5, 10):
        for TreeCls, checker in [(BT, check_btree), (BPT, check_bplustree), (BST, check_btree)]:
            t = TreeCls(d)
            pairs = [(i, i * 10) for i in range(1, 201)]
            for k, v in pairs:
                t.insert(k, v)
            v_list = checker(t, f"{TreeCls.__name__} d={d} seq")
            if v_list:
                fail(name, str(v_list))
                return
            errs = search_all(t, pairs)
            if errs:
                fail(name, str(errs[:3]))
                return
    ok(name)

# --- 5. Reverse insert ---
def test_reverse_insert():
    name = "reverse insert invariants"
    for d in (3, 5):
        for TreeCls, checker in [(BT, check_btree), (BPT, check_bplustree), (BST, check_btree)]:
            t = TreeCls(d)
            pairs = [(i, i) for i in range(200, 0, -1)]
            for k, v in pairs:
                t.insert(k, v)
            v_list = checker(t, f"{TreeCls.__name__} d={d} rev")
            if v_list:
                fail(name, str(v_list))
                return
            errs = search_all(t, pairs)
            if errs:
                fail(name, str(errs[:3]))
                return
    ok(name)

# --- 6. Random insert ---
def test_random_insert():
    name = "random insert invariants"
    rng = random.Random(42)
    keys = rng.sample(range(1, 100001), 1000)
    pairs = [(k, i) for i, k in enumerate(keys)]
    for d in (3, 5, 10):
        for TreeCls, checker in [(BT, check_btree), (BPT, check_bplustree), (BST, check_btree)]:
            t = TreeCls(d)
            for k, v in pairs:
                t.insert(k, v)
            v_list = checker(t, f"{TreeCls.__name__} d={d} rnd")
            if v_list:
                fail(name, str(v_list[:3]))
                return
            errs = search_all(t, pairs)
            if errs:
                fail(name, str(errs[:3]))
                return
    ok(name)

# --- 7. Delete leaf key (no underflow) ---
def test_delete_simple():
    name = "delete simple (no underflow)"
    for TreeCls, checker in [(BT, check_btree), (BPT, check_bplustree), (BST, check_btree)]:
        t = TreeCls(3)
        # Insert enough so tree is full but won't underflow on one delete
        pairs = [(i, i) for i in range(1, 50)]
        for k, v in pairs:
            t.insert(k, v)
        t.delete(25)
        if t.search(25) is not None:
            fail(name, f"[{TreeCls.__name__}] deleted key 25 still found")
            return
        v_list = checker(t, TreeCls.__name__)
        if v_list:
            fail(name, str(v_list))
            return
    ok(name)

# --- 8. Delete nonexistent key ---
def test_delete_nonexistent():
    name = "delete nonexistent key returns False"
    for TreeCls in (BT, BPT, BST):
        t = TreeCls(3)
        for i in range(1, 20):
            t.insert(i, i)
        r = t.delete(999)
        if r is not False:
            fail(name, f"[{TreeCls.__name__}] expected False, got {r}")
            return
    ok(name)

# --- 9. Delete all keys ---
def test_delete_all():
    name = "delete all keys"
    rng = random.Random(7)
    keys = list(range(1, 101))
    for d in (3, 5):
        for TreeCls, checker in [(BT, check_btree), (BPT, check_bplustree), (BST, check_btree)]:
            t = TreeCls(d)
            for k in keys:
                t.insert(k, k)
            rng.shuffle(keys)
            for k in keys:
                t.delete(k)
                v_list = checker(t, f"{TreeCls.__name__} d={d} del-all step")
                if v_list:
                    fail(name, f"[{TreeCls.__name__} d={d}] after deleting {k}: {v_list}")
                    return
                if t.search(k) is not None:
                    fail(name, f"[{TreeCls.__name__}] deleted key {k} still found")
                    return
            # tree should be empty
            for k in keys:
                if t.search(k) is not None:
                    fail(name, f"[{TreeCls.__name__}] key {k} found in empty tree")
                    return
    ok(name)

# --- 10. Delete causing borrow from left sibling ---
def test_delete_borrow_left():
    name = "delete triggers borrow from left sibling"
    # Build a tree where borrow-from-left is forced
    for d in (2, 3):
        for TreeCls, checker in [(BT, check_btree), (BPT, check_bplustree), (BST, check_btree)]:
            t = TreeCls(d)
            keys = list(range(1, 4 * d * d + 1))
            for k in keys:
                t.insert(k, k)
            # delete from the right portion repeatedly to trigger borrows
            to_delete = keys[len(keys)//2:]
            random.shuffle(to_delete)
            for k in to_delete:
                t.delete(k)
                v_list = checker(t, f"{TreeCls.__name__} d={d}")
                if v_list:
                    fail(name, str(v_list))
                    return
    ok(name)

# --- 11. Delete causing merge ---
def test_delete_merge():
    name = "delete triggers merge"
    for d in (2, 3):
        for TreeCls, checker in [(BT, check_btree), (BPT, check_bplustree), (BST, check_btree)]:
            t = TreeCls(d)
            # Insert just enough to build multi-level tree
            keys = list(range(1, 6 * d + 1))
            for k in keys:
                t.insert(k, k)
            # Delete most of them to force merges
            to_del = keys[:len(keys) * 3 // 4]
            random.shuffle(to_del)
            for k in to_del:
                t.delete(k)
                v_list = checker(t, f"{TreeCls.__name__} d={d}")
                if v_list:
                    fail(name, f"after deleting {k}: {v_list}")
                    return
    ok(name)

# --- 12. Delete internal node key ---
def test_delete_internal_key():
    name = "delete key at internal node"
    for d in (2, 3):
        for TreeCls, checker in [(BT, check_btree), (BPT, check_bplustree), (BST, check_btree)]:
            t = TreeCls(d)
            keys = list(range(1, 30))
            for k in keys:
                t.insert(k, k)
            # Try to delete keys that are likely separator keys in internal nodes
            for k in [8, 15, 20, 5, 25]:
                if k in keys:
                    t.delete(k)
                    if t.search(k) is not None:
                        fail(name, f"[{TreeCls.__name__} d={d}] deleted internal key {k} still found")
                        return
                    v_list = checker(t, f"{TreeCls.__name__} d={d}")
                    if v_list:
                        fail(name, str(v_list))
                        return
    ok(name)

# --- 13. Insert after delete ---
def test_insert_after_delete():
    name = "insert after delete"
    rng = random.Random(13)
    for TreeCls, checker in [(BT, check_btree), (BPT, check_bplustree), (BST, check_btree)]:
        t = TreeCls(3)
        keys = list(range(1, 101))
        for k in keys:
            t.insert(k, k)
        to_del = rng.sample(keys, 40)
        for k in to_del:
            t.delete(k)
        # Now re-insert deleted keys
        for k in to_del:
            t.insert(k, k * 100)
        v_list = checker(t, TreeCls.__name__)
        if v_list:
            fail(name, str(v_list))
            return
        # Verify all
        for k in keys:
            expected = k * 100 if k in to_del else k
            r = t.search(k)
            if r != expected:
                fail(name, f"[{TreeCls.__name__}] search({k}): expected {expected}, got {r}")
                return
    ok(name)

# --- 14. B+-tree range query correctness ---
def test_bpt_range_query():
    name = "B+-tree range query correctness"
    for d in (2, 3, 5):
        t = BPT(d)
        keys = list(range(1, 201))
        for k in keys:
            t.insert(k, k * 10)
        # Range [50, 100]
        results = t.range_query(50, 100)
        result_keys = sorted(k for k, _ in results)
        expected = list(range(50, 101))
        if result_keys != expected:
            fail(name, f"d={d}: got {result_keys[:5]}... expected {expected[:5]}...")
            return
        # Check RIDs
        for k, rid in results:
            if rid != k * 10:
                fail(name, f"d={d}: key {k} has rid {rid}, expected {k*10}")
                return
        # Empty range
        results = t.range_query(500, 600)
        if results:
            fail(name, f"d={d}: range [500,600] should be empty, got {results}")
            return
        # Single element range
        results = t.range_query(77, 77)
        if len(results) != 1 or results[0][0] != 77:
            fail(name, f"d={d}: range [77,77] should return [(77,...)], got {results}")
            return
    ok(name)

# --- 15. B+-tree range query after deletions ---
def test_bpt_range_after_delete():
    name = "B+-tree range query after deletions"
    rng = random.Random(99)
    d = 3
    t = BPT(d)
    keys = list(range(1, 201))
    for k in keys:
        t.insert(k, k)
    to_del = rng.sample(keys, 50)
    for k in to_del:
        t.delete(k)
    remaining = sorted(set(keys) - set(to_del))
    # Range [1, 200]
    results = t.range_query(1, 200)
    result_keys = sorted(k for k, _ in results)
    if result_keys != remaining:
        missing = set(remaining) - set(result_keys)
        extra = set(result_keys) - set(remaining)
        fail(name, f"missing={list(missing)[:5]}, extra={list(extra)[:5]}")
        return
    ok(name)

# --- 16. B*-tree: redistribution fires before split ---
def test_bst_redistribution():
    name = "B*-tree redistribution reduces splits vs B-tree"
    d = 3
    bt = BT(d)
    bst = BST(d)
    keys = list(range(1, 301))
    for k in keys:
        bt.insert(k, k)
        bst.insert(k, k)
    # B*-tree should have fewer splits and fewer nodes
    if bst.split_count >= bt.split_count:
        fail(name, f"BST splits={bst.split_count} >= BT splits={bt.split_count}")
        return
    if bst.node_count() >= bt.node_count():
        fail(name, f"BST nodes={bst.node_count()} >= BT nodes={bt.node_count()}")
        return
    ok(name)

# --- 17. Large random stress test with invariant check every N ops ---
def test_stress():
    name = "stress: 2000 random inserts + 1000 deletes, invariants checked"
    rng = random.Random(2024)
    all_keys = rng.sample(range(1, 50001), 2000)
    d = 3
    for TreeCls, checker in [(BT, check_btree), (BPT, check_bplustree), (BST, check_btree)]:
        t = TreeCls(d)
        inserted = {}
        for i, k in enumerate(all_keys):
            t.insert(k, i)
            inserted[k] = i
            if (i + 1) % 200 == 0:
                v_list = checker(t, f"{TreeCls.__name__} after {i+1} inserts")
                if v_list:
                    fail(name, str(v_list[:2]))
                    return

        # Verify all inserted keys found
        for k, v in inserted.items():
            if t.search(k) != v:
                fail(name, f"[{TreeCls.__name__}] search({k}) wrong after all inserts")
                return

        # Delete 1000 random keys
        to_del = rng.sample(list(inserted.keys()), 1000)
        for i, k in enumerate(to_del):
            t.delete(k)
            del inserted[k]
            if (i + 1) % 200 == 0:
                v_list = checker(t, f"{TreeCls.__name__} after {i+1} deletes")
                if v_list:
                    fail(name, str(v_list[:2]))
                    return

        # Verify remaining
        for k, v in inserted.items():
            if t.search(k) != v:
                fail(name, f"[{TreeCls.__name__}] search({k}) wrong after deletes")
                return

        # Verify deleted keys gone
        for k in to_del:
            if t.search(k) is not None:
                fail(name, f"[{TreeCls.__name__}] deleted key {k} still found")
                return

    ok(name)

# --- 18. Invariant: every-step check on small tree ---
def test_every_step_invariant():
    name = "every-step invariant on 50 inserts + 50 deletes"
    rng = random.Random(17)
    keys = rng.sample(range(1, 500), 50)
    for d in (2, 3):
        for TreeCls, checker in [(BT, check_btree), (BPT, check_bplustree), (BST, check_btree)]:
            t = TreeCls(d)
            inserted = []
            for k in keys:
                t.insert(k, k)
                inserted.append(k)
                v_list = checker(t, f"{TreeCls.__name__} d={d}")
                if v_list:
                    fail(name, f"insert({k}): {v_list}")
                    return
            rng.shuffle(inserted)
            for k in inserted:
                t.delete(k)
                v_list = checker(t, f"{TreeCls.__name__} d={d}")
                if v_list:
                    fail(name, f"delete({k}): {v_list}")
                    return
    ok(name)

# --- 19. B+-tree leaf list integrity after stress ---
def test_bpt_leaf_list_stress():
    name = "B+-tree leaf list integrity under stress"
    rng = random.Random(55)
    t = BPT(3)
    keys = list(range(1, 501))
    for k in keys:
        t.insert(k, k)
    to_del = rng.sample(keys, 200)
    for k in to_del:
        t.delete(k)
    v_list = check_bplustree(t, "BPT leaf-list stress")
    if v_list:
        fail(name, str(v_list))
        return
    # Traverse linked list and collect all keys
    node = t.root
    while not node.is_leaf:
        node = node.children[0]
    leaf_keys = []
    while node:
        leaf_keys.extend(node.keys)
        node = node.next
    expected = sorted(set(keys) - set(to_del))
    if leaf_keys != expected:
        missing = set(expected) - set(leaf_keys)
        extra = set(leaf_keys) - set(expected)
        fail(name, f"leaf list mismatch: missing={list(missing)[:5]}, extra={list(extra)[:5]}")
        return
    ok(name)

# --- 20. node_count and utilization are consistent ---
def test_metrics_consistent():
    name = "node_count and utilization consistent"
    for TreeCls in (BT, BPT, BST):
        t = TreeCls(3)
        for k in range(1, 101):
            t.insert(k, k)
        nc = t.node_count()
        util = t.utilization()
        if nc <= 0:
            fail(name, f"[{TreeCls.__name__}] node_count={nc}")
            return
        if not (0.0 < util <= 1.0):
            fail(name, f"[{TreeCls.__name__}] utilization={util}")
            return
    ok(name)

# --- 21. Search for keys never inserted returns None ---
def test_search_not_found():
    name = "search for non-inserted key returns None"
    for TreeCls in (BT, BPT, BST):
        t = TreeCls(3)
        for k in range(1, 100, 2):  # odd numbers
            t.insert(k, k)
        for k in range(2, 100, 2):  # even numbers (not inserted)
            r = t.search(k)
            if r is not None:
                fail(name, f"[{TreeCls.__name__}] search({k}) = {r}, expected None")
                return
    ok(name)

# --- 22. Large d value ---
def test_large_order():
    name = "large order d=50"
    for TreeCls, checker in [(BT, check_btree), (BPT, check_bplustree), (BST, check_btree)]:
        t = TreeCls(50)
        keys = list(range(1, 1001))
        for k in keys:
            t.insert(k, k)
        v_list = checker(t, f"{TreeCls.__name__} d=50")
        if v_list:
            fail(name, str(v_list))
            return
        for k in range(1, 1001, 7):
            t.delete(k)
        v_list = checker(t, f"{TreeCls.__name__} d=50 post-delete")
        if v_list:
            fail(name, str(v_list))
            return
    ok(name)

# ---------------------------------------------------------------------------
# Runner
# ---------------------------------------------------------------------------

TESTS = [
    ("01 empty search",                  test_empty_search),
    ("02 single insert/search",          test_single),
    ("03 duplicate insert",              test_duplicate_insert),
    ("04 sequential insert invariants",  test_sequential_insert),
    ("05 reverse insert",                test_reverse_insert),
    ("06 random insert",                 test_random_insert),
    ("07 delete simple",                 test_delete_simple),
    ("08 delete nonexistent",            test_delete_nonexistent),
    ("09 delete all keys",               test_delete_all),
    ("10 delete borrow left",            test_delete_borrow_left),
    ("11 delete merge",                  test_delete_merge),
    ("12 delete internal key",           test_delete_internal_key),
    ("13 insert after delete",           test_insert_after_delete),
    ("14 B+-tree range query",           test_bpt_range_query),
    ("15 B+-tree range after delete",    test_bpt_range_after_delete),
    ("16 B*-tree redistribution",        test_bst_redistribution),
    ("17 stress test",                   test_stress),
    ("18 every-step invariant",          test_every_step_invariant),
    ("19 B+-tree leaf list stress",      test_bpt_leaf_list_stress),
    ("20 metrics consistent",            test_metrics_consistent),
    ("21 search not found",              test_search_not_found),
    ("22 large order d=50",              test_large_order),
]


def main():
    print("=" * 60)
    print("CSE321 B-tree Correctness Test Suite")
    print("=" * 60)
    for label, fn in TESTS:
        run_test(label, fn)
    print("=" * 60)
    print(f"Results: {PASS} passed, {FAIL} failed out of {PASS + FAIL} tests")
    print("=" * 60)
    sys.exit(1 if FAIL > 0 else 0)


if __name__ == "__main__":
    main()

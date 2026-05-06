# CSE321 Project #1 — B-tree Index Structures

Implementation and experimental analysis of B-tree, B\*-tree, and B+-tree index structures.
Built for CSE321 (Database Systems), UNIST, Spring 2026.

## Requirements

- Python 3.9 or later
- No external dependencies (standard library only)

## File Structure

```
repo-root/
├── student.csv       # Dataset (100,000 records)
├── interfaces.py     # Abstract base class for all tree implementations
├── utils.py          # Binary search helpers (find_index, find_right_index)
├── btree.py          # B-tree (order d)
├── bplustree.py      # B+-tree (leaf linked list, copy-up split)
├── bstartree.py      # B*-tree (extends BT; insert-time redistribution + 2-to-3 split)
├── experiment.py     # Runs all four experiments and prints results
├── test_trees.py     # Correctness tests
└── README.md
```

## Running the Experiments

```bash
# uses student.csv in the same directory (default)
python experiment.py

# or specify the dataset path explicitly
python experiment.py /path/to/student.csv
```

Runs all four experiments sequentially and prints results to stdout.

## Running the Tests

```bash
python test_trees.py
```

## Experiments

| # | Name | Description |
|---|------|-------------|
| 1 | Insertion & Parameter Tuning | Insert all 100,000 records; measure time, node count, split count, and utilization for d = 3, 5, 10 |
| 2 | Point Search | 10,000 random key lookups; measure mean time per query |
| 3 | Range Query | Average GPA and height of male students with ID in [202000000, 202099999] |
| 4 | Deletion | Delete 10% and 20% of records; measure time, node count, and post-deletion utilization |

import csv
import random
import time
import sys
import os

from interfaces import BaseTree
from btree import BT
from bplustree import BPT
from bstartree import BST


def load_records(csv_path):
    records = []
    with open(csv_path, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            records.append({
                'id': int(row['Student ID']),
                'name': row['Name'],
                'gender': row['Gender'],
                'gpa': float(row['GPA']),
                'height': float(row['Height']),
                'weight': float(row['Weight']),
            })
    id_list = [r['id'] for r in records]
    return records, id_list


def make_trees(order) -> dict[str, BaseTree]:
    return {
        'B-tree':  BT(order),
        'B*-tree': BST(order),
        'B+-tree': BPT(order),
    }


def exp_insertion(records, id_list, orders=(3, 5, 10)):
    print("\n========== Experiment 1: Insertion & Parameter Tuning ==========")
    print(f"{'Tree':<10} {'d':>4} {'Time(s)':>10} {'Nodes':>8} {'Splits':>8} {'Util%':>8}")
    print("-" * 55)

    insertion_results = {}
    for order in orders:
        trees = make_trees(order)
        for name, tree in trees.items():
            tree.split_count = 0
            start_time = time.perf_counter()
            for record_id, record in enumerate(records):
                tree.insert(record['id'], record_id)
            elapsed = time.perf_counter() - start_time

            node_count = tree.node_count()
            split_count = tree.split_count
            util = tree.utilization() * 100
            print(f"{name:<10} {order:>4} {elapsed:>10.4f} {node_count:>8} {split_count:>8} {util:>8.1f}")
            insertion_results[(name, order)] = {
                'time': elapsed, 'nodes': node_count,
                'splits': split_count, 'util': util, 'tree': tree,
            }
        print()
    return insertion_results


def exp_point_search(insertion_results, id_list, num_queries=10000, orders=(3, 5, 10)):
    print("\n========== Experiment 2: Point Search ==========")
    random.seed(2024)
    query_keys = random.sample(id_list, num_queries)

    print(f"{'Tree':<10} {'d':>4} {'Mean(us)':>10}")
    print("-" * 28)

    for order in orders:
        trees = {name: insertion_results[(name, order)]['tree'] for name in ['B-tree', 'B*-tree', 'B+-tree']}
        for name, tree in trees.items():
            start_time = time.perf_counter()
            for key in query_keys:
                tree.search(key)
            elapsed = time.perf_counter() - start_time
            mean_microseconds = elapsed / num_queries * 1e6
            print(f"{name:<10} {order:>4} {mean_microseconds:>10.3f}")
        print()


def exp_range_query(insertion_results, records, orders=(3, 5, 10)):
    print("\n========== Experiment 3: Range Query ==========")
    START_ID = 202000000
    END_ID   = 202099999
    print(f"Query: avg GPA and height of male students, ID in [{START_ID}, {END_ID}]")
    print(f"{'Tree':<10} {'d':>4} {'Time(ms)':>10} {'Count':>8} {'AvgGPA':>8} {'AvgHt':>8}")
    print("-" * 55)

    for order in orders:
        trees = {name: insertion_results[(name, order)]['tree'] for name in ['B-tree', 'B*-tree', 'B+-tree']}
        for name, tree in trees.items():
            start_time = time.perf_counter()

            pairs = tree.range_query(START_ID, END_ID)
            record_ids = [rid for _, rid in pairs]

            gpa_values, heights = [], []
            for rid in record_ids:
                r = records[rid]
                if r['gender'] == 'Male':
                    gpa_values.append(r['gpa'])
                    heights.append(r['height'])

            elapsed = (time.perf_counter() - start_time) * 1000
            average_gpa = sum(gpa_values) / len(gpa_values) if gpa_values else 0
            average_height = sum(heights) / len(heights) if heights else 0
            print(f"{name:<10} {order:>4} {elapsed:>10.3f} {len(gpa_values):>8} {average_gpa:>8.3f} {average_height:>8.2f}")
        print()


def exp_deletion(insertion_results, id_list, orders=(3, 5, 10)):
    print("\n========== Experiment 4: Deletion & Structural Integrity ==========")
    random.seed(13)

    percentages = [0.10, 0.20]
    print(f"{'Tree':<10} {'d':>4} {'Del%':>6} {'Time(s)':>10} {'Nodes':>8} {'Util%':>8}")
    print("-" * 55)

    for order in orders:
        for pct in percentages:
            deletion_keys = random.sample(id_list, int(len(id_list) * pct))

            trees_fresh = make_trees(order)
            for tree in trees_fresh.values():
                for rid, sid in enumerate(id_list):
                    tree.insert(sid, rid)

            for name, tree in trees_fresh.items():
                start_time = time.perf_counter()
                for key in deletion_keys:
                    tree.delete(key)
                elapsed = time.perf_counter() - start_time
                node_count = tree.node_count()
                util = tree.utilization() * 100
                print(f"{name:<10} {order:>4} {pct*100:>5.0f}% {elapsed:>10.4f} {node_count:>8} {util:>8.1f}")
        print()


def main():
    default_csv = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'student.csv')
    csv_path = os.path.abspath(sys.argv[1] if len(sys.argv) > 1 else default_csv)

    print(f"Loading records from: {csv_path}")
    records, id_list = load_records(csv_path)
    print(f"Loaded {len(records)} records.\n")

    orders = (3, 5, 10)
    insertion_results = exp_insertion(records, id_list, orders)
    exp_point_search(insertion_results, id_list, num_queries=10000, orders=orders)
    exp_range_query(insertion_results, records, orders)
    exp_deletion(insertion_results, id_list, orders)

    print("\nAll experiments done.")


if __name__ == '__main__':
    main()

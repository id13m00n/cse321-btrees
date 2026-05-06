from utils import find_index, find_right_index
from interfaces import BaseTree


class BTNode:
    def __init__(self, is_leaf=False):
        self.keys = []
        self.record_ids = []
        self.children = []
        self.is_leaf = is_leaf


class BT(BaseTree):
    def __init__(self, order):
        self.order = order
        self.root = self._make_node(is_leaf=True)
        self.split_count = 0

    def _make_node(self, is_leaf):
        return BTNode(is_leaf=is_leaf)

    def search(self, key):
        return self._search(self.root, key)

    def _search(self, node, key):
        index = find_index(node.keys, key)
        if index < len(node.keys) and node.keys[index] == key:
            return node.record_ids[index]
        if node.is_leaf:
            return None
        return self._search(node.children[index], key)

    def insert(self, key, record_id):
        overflow = self._insert(self.root, key, record_id)
        if overflow:
            middle_key, middle_record_id, new_node = overflow
            new_root = self._make_node(is_leaf=False)
            new_root.keys = [middle_key]
            new_root.record_ids = [middle_record_id]
            new_root.children = [self.root, new_node]
            self.root = new_root

    def _insert(self, node, key, record_id):
        index = find_index(node.keys, key)

        if index < len(node.keys) and node.keys[index] == key:
            node.record_ids[index] = record_id
            return None

        if node.is_leaf:
            node.keys.insert(index, key)
            node.record_ids.insert(index, record_id)
        else:
            overflow = self._insert(node.children[index], key, record_id)
            if overflow:
                middle_key, middle_record_id, new_child = overflow
                node.keys.insert(index, middle_key)
                node.record_ids.insert(index, middle_record_id)
                node.children.insert(index + 1, new_child)

        if len(node.keys) > 2 * self.order:
            return self._split(node)
        return None

    def _split(self, node):
        self.split_count += 1
        middle_index = self.order

        new_node = self._make_node(is_leaf=node.is_leaf)
        middle_key = node.keys[middle_index]
        middle_record_id = node.record_ids[middle_index]

        new_node.keys = node.keys[middle_index + 1:]
        new_node.record_ids = node.record_ids[middle_index + 1:]
        if not node.is_leaf:
            new_node.children = node.children[middle_index + 1:]

        node.keys = node.keys[:middle_index]
        node.record_ids = node.record_ids[:middle_index]
        if not node.is_leaf:
            node.children = node.children[:middle_index + 1]

        return middle_key, middle_record_id, new_node

    def delete(self, key):
        found = self._delete(self.root, key)
        if not self.root.is_leaf and len(self.root.keys) == 0:
            self.root = self.root.children[0]
        return found

    def _delete(self, node, key):
        index = find_index(node.keys, key)

        if node.is_leaf:
            if index < len(node.keys) and node.keys[index] == key:
                node.keys.pop(index)
                node.record_ids.pop(index)
                return True
            return False

        if index < len(node.keys) and node.keys[index] == key:
            # Replace with in-order predecessor and delete it from the left subtree.
            # Bottom-up fix in _delete_from_child handles any underflow that results.
            repl_key, repl_rid = self._max_leaf_entry(node.children[index])
            node.keys[index] = repl_key
            node.record_ids[index] = repl_rid
            return self._delete_from_child(node, index, repl_key)

        return self._delete_from_child(node, index, key)

    def _delete_from_child(self, parent, child_index, key):
        found = self._delete(parent.children[child_index], key)
        # Bottom-up underflow fix: check after deletion, not before.
        if len(parent.children[child_index].keys) < self.order:
            self._fix_child(parent, child_index)
        return found

    def _fix_child(self, parent, child_index):
        child = parent.children[child_index]
        left_sib = parent.children[child_index - 1] if child_index > 0 else None
        right_sib = parent.children[child_index + 1] if child_index < len(parent.children) - 1 else None

        if left_sib and len(left_sib.keys) > self.order:
            child.keys.insert(0, parent.keys[child_index - 1])
            child.record_ids.insert(0, parent.record_ids[child_index - 1])
            parent.keys[child_index - 1] = left_sib.keys.pop()
            parent.record_ids[child_index - 1] = left_sib.record_ids.pop()
            if not child.is_leaf:
                child.children.insert(0, left_sib.children.pop())
            return child_index

        if right_sib and len(right_sib.keys) > self.order:
            child.keys.append(parent.keys[child_index])
            child.record_ids.append(parent.record_ids[child_index])
            parent.keys[child_index] = right_sib.keys.pop(0)
            parent.record_ids[child_index] = right_sib.record_ids.pop(0)
            if not child.is_leaf:
                child.children.append(right_sib.children.pop(0))
            return child_index

        merge_index = child_index if right_sib else child_index - 1
        self._merge_children(parent, merge_index)
        return merge_index

    def _merge_children(self, parent, index):
        left_child = parent.children[index]
        right_child = parent.children[index + 1]
        left_child.keys.append(parent.keys[index])
        left_child.record_ids.append(parent.record_ids[index])
        left_child.keys.extend(right_child.keys)
        left_child.record_ids.extend(right_child.record_ids)
        if not left_child.is_leaf:
            left_child.children.extend(right_child.children)
        parent.keys.pop(index)
        parent.record_ids.pop(index)
        parent.children.pop(index + 1)

    def _max_leaf_entry(self, node):
        while not node.is_leaf:
            node = node.children[-1]
        return node.keys[-1], node.record_ids[-1]

    def _min_leaf_entry(self, node):
        while not node.is_leaf:
            node = node.children[0]
        return node.keys[0], node.record_ids[0]

    def range_query(self, start_key, end_key):
        results = []
        self._range(self.root, start_key, end_key, results)
        return results

    def _range(self, node, start_key, end_key, results):
        i = find_index(node.keys, start_key)
        if not node.is_leaf:
            self._range(node.children[i], start_key, end_key, results)
        while i < len(node.keys):
            if node.keys[i] > end_key:
                return
            results.append((node.keys[i], node.record_ids[i]))
            if not node.is_leaf:
                self._range(node.children[i + 1], start_key, end_key, results)
            i += 1

    def node_count(self):
        return self._count(self.root)

    def _count(self, node):
        count = 1
        for child in node.children:
            count += self._count(child)
        return count

    def utilization(self):
        capacity, fill = self._util(self.root)
        return fill / capacity if capacity > 0 else 0.0

    def _util(self, node):
        capacity = 2 * self.order
        fill = len(node.keys)
        for child in node.children:
            child_capacity, child_fill = self._util(child)
            capacity += child_capacity
            fill += child_fill
        return capacity, fill

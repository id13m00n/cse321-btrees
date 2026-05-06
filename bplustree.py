from utils import find_index, find_right_index
from interfaces import BaseTree


class BPTNode:
    def __init__(self, is_leaf=False):
        self.keys = []
        self.children = []
        self.record_ids = []
        self.next = None
        self.is_leaf = is_leaf


class BPT(BaseTree):
    def __init__(self, order):
        self.order = order
        self.root = BPTNode(is_leaf=True)
        self.split_count = 0

    def search(self, key):
        leaf = self._find_leaf(key)
        index = find_index(leaf.keys, key)
        if index < len(leaf.keys) and leaf.keys[index] == key:
            return leaf.record_ids[index]
        return None

    def _find_leaf(self, key):
        node = self.root
        while not node.is_leaf:
            index = find_right_index(node.keys, key)
            node = node.children[index]
        return node

    def insert(self, key, record_id):
        result = self._insert(self.root, key, record_id)
        if result:
            separator_key, new_child = result
            new_root = BPTNode(is_leaf=False)
            new_root.keys = [separator_key]
            new_root.children = [self.root, new_child]
            self.root = new_root

    def _insert(self, node, key, record_id):
        if node.is_leaf:
            index = find_index(node.keys, key)
            if index < len(node.keys) and node.keys[index] == key:
                node.record_ids[index] = record_id
                return None
            node.keys.insert(index, key)
            node.record_ids.insert(index, record_id)
            if len(node.keys) > 2 * self.order:
                return self._split_leaf(node)
            return None

        index = find_right_index(node.keys, key)
        result = self._insert(node.children[index], key, record_id)
        if result:
            separator_key, new_child = result
            node.keys.insert(index, separator_key)
            node.children.insert(index + 1, new_child)
            if len(node.keys) > 2 * self.order:
                return self._split_internal(node)
        return None

    def _split_leaf(self, leaf):
        self.split_count += 1
        middle_index = self.order
        new_leaf = BPTNode(is_leaf=True)
        new_leaf.keys = leaf.keys[middle_index:]
        new_leaf.record_ids = leaf.record_ids[middle_index:]
        new_leaf.next = leaf.next
        leaf.next = new_leaf
        leaf.keys = leaf.keys[:middle_index]
        leaf.record_ids = leaf.record_ids[:middle_index]
        return new_leaf.keys[0], new_leaf

    def _split_internal(self, node):
        self.split_count += 1
        middle_index = self.order
        new_node = BPTNode(is_leaf=False)
        separator_key = node.keys[middle_index]
        new_node.keys = node.keys[middle_index + 1:]
        new_node.children = node.children[middle_index + 1:]
        node.keys = node.keys[:middle_index]
        node.children = node.children[:middle_index + 1]
        return separator_key, new_node

    def delete(self, key):
        found = self._delete(self.root, key)
        if not self.root.is_leaf and len(self.root.keys) == 0:
            self.root = self.root.children[0]
        return found

    def _delete(self, node, key):
        if node.is_leaf:
            index = find_index(node.keys, key)
            if index < len(node.keys) and node.keys[index] == key:
                node.keys.pop(index)
                node.record_ids.pop(index)
                return True
            return False

        index = find_right_index(node.keys, key)
        found = self._delete(node.children[index], key)
        # Bottom-up underflow fix: check after deletion, not before.
        if len(node.children[index].keys) < self.order:
            self._fix_child(node, index)
        return found

    def _fix_child(self, parent, child_index):
        child = parent.children[child_index]
        left_sib = parent.children[child_index - 1] if child_index > 0 else None
        right_sib = parent.children[child_index + 1] if child_index < len(parent.children) - 1 else None

        if left_sib and len(left_sib.keys) > self.order:
            if child.is_leaf:
                child.keys.insert(0, left_sib.keys.pop())
                child.record_ids.insert(0, left_sib.record_ids.pop())
                parent.keys[child_index - 1] = child.keys[0]
            else:
                child.keys.insert(0, parent.keys[child_index - 1])
                parent.keys[child_index - 1] = left_sib.keys.pop()
                child.children.insert(0, left_sib.children.pop())
            return child_index

        if right_sib and len(right_sib.keys) > self.order:
            if child.is_leaf:
                child.keys.append(right_sib.keys.pop(0))
                child.record_ids.append(right_sib.record_ids.pop(0))
                parent.keys[child_index] = right_sib.keys[0]
            else:
                child.keys.append(parent.keys[child_index])
                parent.keys[child_index] = right_sib.keys.pop(0)
                child.children.append(right_sib.children.pop(0))
            return child_index

        merge_index = child_index if right_sib else child_index - 1
        self._merge(parent, merge_index)
        return merge_index

    def _merge(self, parent, index):
        left_child = parent.children[index]
        right_child = parent.children[index + 1]
        if left_child.is_leaf:
            left_child.keys.extend(right_child.keys)
            left_child.record_ids.extend(right_child.record_ids)
            left_child.next = right_child.next
        else:
            left_child.keys.append(parent.keys[index])
            left_child.keys.extend(right_child.keys)
            left_child.children.extend(right_child.children)
        parent.keys.pop(index)
        parent.children.pop(index + 1)

    def range_query(self, start_key, end_key):
        results = []
        node = self._find_leaf(start_key)
        while node is not None:
            for index, key in enumerate(node.keys):
                if key > end_key:
                    return results
                if key >= start_key:
                    results.append((key, node.record_ids[index]))
            node = node.next
        return results

    def node_count(self):
        return self._count(self.root)

    def _count(self, node):
        count = 1
        if not node.is_leaf:
            for child in node.children:
                count += self._count(child)
        return count

    def utilization(self):
        capacity, fill = self._util(self.root)
        return fill / capacity if capacity > 0 else 0.0

    def _util(self, node):
        capacity = 2 * self.order
        fill = len(node.keys)
        if not node.is_leaf:
            for child in node.children:
                child_capacity, child_fill = self._util(child)
                capacity += child_capacity
                fill += child_fill
        return capacity, fill

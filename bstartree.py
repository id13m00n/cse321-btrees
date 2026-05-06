from btree import BT, BTNode
from utils import find_index


class BST(BT):
    def __init__(self, order):
        super().__init__(order)

    def insert(self, key, record_id):
        path = []
        node = self.root

        while not node.is_leaf:
            index = find_index(node.keys, key)
            if index < len(node.keys) and node.keys[index] == key:
                node.record_ids[index] = record_id
                return
            path.append((node, index))
            node = node.children[index]

        index = find_index(node.keys, key)
        if index < len(node.keys) and node.keys[index] == key:
            node.record_ids[index] = record_id
            return
        node.keys.insert(index, key)
        node.record_ids.insert(index, record_id)

        overflow_node = node
        while len(overflow_node.keys) > 2 * self.order:
            if not path:
                middle_key, middle_record_id, new_node = self._split(overflow_node)
                new_root = BTNode(is_leaf=False)
                new_root.keys = [middle_key]
                new_root.record_ids = [middle_record_id]
                new_root.children = [self.root, new_node]
                self.root = new_root
                return

            parent, child_index = path.pop()
            left_sib = parent.children[child_index - 1] if child_index > 0 else None
            right_sib = parent.children[child_index + 1] if child_index < len(parent.children) - 1 else None

            if left_sib and len(left_sib.keys) < 2 * self.order:
                self._redistribute_to_left(parent, child_index)
                return
            if right_sib and len(right_sib.keys) < 2 * self.order:
                self._redistribute_to_right(parent, child_index)
                return

            self._split_2to3(parent, child_index - 1 if left_sib else child_index)
            overflow_node = parent

    def _redistribute_to_left(self, parent, child_index):
        overflow_node = parent.children[child_index]
        left_sib = parent.children[child_index - 1]
        left_sib.keys.append(parent.keys[child_index - 1])
        left_sib.record_ids.append(parent.record_ids[child_index - 1])
        parent.keys[child_index - 1] = overflow_node.keys.pop(0)
        parent.record_ids[child_index - 1] = overflow_node.record_ids.pop(0)
        if not overflow_node.is_leaf:
            left_sib.children.append(overflow_node.children.pop(0))

    def _redistribute_to_right(self, parent, child_index):
        overflow_node = parent.children[child_index]
        right_sib = parent.children[child_index + 1]
        right_sib.keys.insert(0, parent.keys[child_index])
        right_sib.record_ids.insert(0, parent.record_ids[child_index])
        parent.keys[child_index] = overflow_node.keys.pop()
        parent.record_ids[child_index] = overflow_node.record_ids.pop()
        if not overflow_node.is_leaf:
            right_sib.children.insert(0, overflow_node.children.pop())

    # Assistance from AI, but not copied by AI.
    def _split_2to3(self, parent, left_index):
        self.split_count += 1
        left_child = parent.children[left_index]
        right_child = parent.children[left_index + 1]

        all_keys = left_child.keys + [parent.keys[left_index]] + right_child.keys
        all_record_ids = left_child.record_ids + [parent.record_ids[left_index]] + right_child.record_ids
        all_children = (left_child.children + right_child.children) if not left_child.is_leaf else []

        part_size = (len(all_keys) - 2) // 3
        separator1_index = part_size
        separator2_index = 2 * part_size + 1

        middle_node = BTNode(is_leaf=left_child.is_leaf)

        left_child.keys = all_keys[:part_size]
        left_child.record_ids = all_record_ids[:part_size]
        middle_node.keys = all_keys[part_size + 1: separator2_index]
        middle_node.record_ids = all_record_ids[part_size + 1: separator2_index]
        right_child.keys = all_keys[separator2_index + 1:]
        right_child.record_ids = all_record_ids[separator2_index + 1:]

        if not left_child.is_leaf:
            left_child.children = all_children[:part_size + 1]
            middle_node.children = all_children[part_size + 1: 2 * part_size + 2]
            right_child.children = all_children[2 * part_size + 2:]

        parent.keys[left_index] = all_keys[separator2_index]
        parent.record_ids[left_index] = all_record_ids[separator2_index]
        parent.keys.insert(left_index, all_keys[separator1_index])
        parent.record_ids.insert(left_index, all_record_ids[separator1_index])
        parent.children.insert(left_index + 1, middle_node)

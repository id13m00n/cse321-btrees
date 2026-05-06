def find_index(keys, key):
    low, high = 0, len(keys)
    while low < high:
        mid = (low + high) // 2
        if keys[mid] < key:
            low = mid + 1
        else:
            high = mid
    return low


def find_right_index(keys, key):
    low, high = 0, len(keys)
    while low < high:
        mid = (low + high) // 2
        if keys[mid] <= key:
            low = mid + 1
        else:
            high = mid
    return low

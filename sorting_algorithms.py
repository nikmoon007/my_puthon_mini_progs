"""
Модуль с различными алгоритмами сортировки на Python.
Включает: пузырьковую, быструю, слиянием, вставками, выбором и кучей.
"""

def bubble_sort(arr):
    """
    Пузырьковая сортировка (Bubble Sort).
    Сложность: O(n^2)
    """
    n = len(arr)
    # Копируем массив, чтобы не изменять оригинал
    result = arr[:]
    for i in range(n):
        # Флаг для оптимизации: если обменов не было, массив уже отсортирован
        swapped = False
        for j in range(0, n - i - 1):
            if result[j] > result[j + 1]:
                result[j], result[j + 1] = result[j + 1], result[j]
                swapped = True
        if not swapped:
            break
    return result


def selection_sort(arr):
    """
    Сортировка выбором (Selection Sort).
    Сложность: O(n^2)
    """
    result = arr[:]
    n = len(result)
    for i in range(n):
        min_idx = i
        for j in range(i + 1, n):
            if result[j] < result[min_idx]:
                min_idx = j
        result[i], result[min_idx] = result[min_idx], result[i]
    return result


def insertion_sort(arr):
    """
    Сортировка вставками (Insertion Sort).
    Сложность: O(n^2), но эффективна на почти отсортированных данных.
    """
    result = arr[:]
    for i in range(1, len(result)):
        key = result[i]
        j = i - 1
        while j >= 0 and result[j] > key:
            result[j + 1] = result[j]
            j -= 1
        result[j + 1] = key
    return result


def merge_sort(arr):
    """
    Сортировка слиянием (Merge Sort).
    Сложность: O(n log n)
    """
    if len(arr) <= 1:
        return arr[:]
    
    mid = len(arr) // 2
    left = merge_sort(arr[:mid])
    right = merge_sort(arr[mid:])
    
    return merge(left, right)


def merge(left, right):
    """Вспомогательная функция для слияния двух отсортированных списков."""
    result = []
    i = j = 0
    
    while i < len(left) and j < len(right):
        if left[i] <= right[j]:
            result.append(left[i])
            i += 1
        else:
            result.append(right[j])
            j += 1
            
    result.extend(left[i:])
    result.extend(right[j:])
    return result


def quick_sort(arr):
    """
    Быстрая сортировка (Quick Sort).
    Сложность: O(n log n) в среднем, O(n^2) в худшем случае.
    """
    if len(arr) <= 1:
        return arr[:]
    
    pivot = arr[len(arr) // 2]
    left = [x for x in arr if x < pivot]
    middle = [x for x in arr if x == pivot]
    right = [x for x in arr if x > pivot]
    
    return quick_sort(left) + middle + quick_sort(right)


def heap_sort(arr):
    """
    Пирамидальная сортировка (Heap Sort).
    Сложность: O(n log n)
    """
    result = arr[:]
    n = len(result)
    
    # Построение кучи
    for i in range(n // 2 - 1, -1, -1):
        heapify(result, n, i)
    
    # Извлечение элементов из кучи
    for i in range(n - 1, 0, -1):
        result[i], result[0] = result[0], result[i]
        heapify(result, i, 0)
    
    return result


def heapify(arr, n, i):
    """Вспомогательная функция для поддержания свойства кучи."""
    largest = i
    left = 2 * i + 1
    right = 2 * i + 2
    
    if left < n and arr[left] > arr[largest]:
        largest = left
    
    if right < n and arr[right] > arr[largest]:
        largest = right
    
    if largest != i:
        arr[i], arr[largest] = arr[largest], arr[i]
        heapify(arr, n, largest)


if __name__ == "__main__":
    # Пример использования
    data = [64, 34, 25, 12, 22, 11, 90, 5, 77, 30]
    
    print("Исходный массив:", data)
    print("Пузырьковая:", bubble_sort(data))
    print("Выбором:", selection_sort(data))
    print("Вставками:", insertion_sort(data))
    print("Слиянием:", merge_sort(data))
    print("Быстрая:", quick_sort(data))
    print("Кучей:", heap_sort(data))
    
    # Проверка корректности (все результаты должны быть одинаковыми)
    assert bubble_sort(data) == selection_sort(data) == insertion_sort(data) == \
           merge_sort(data) == quick_sort(data) == heap_sort(data)
    print("\nВсе сортировки работают корректно!")

from __future__ import annotations

"""
JsonExplorer — класс для удобной работы со сложными вложенными JSON-структурами.

Позволяет:
  - Анализировать структуру (ключи, типы, глубина)
  - Искать все пути к ключу или значению
  - Изменять значения по пути или имени ключа
  - Сравнивать несколько структур между собой
  - Экспортировать результаты в CSV и консоль
  - Фильтровать, выравнивать и извлекать данные
"""

import csv
import io
import json
import copy
import sys
from collections import Counter
from typing import Any


class JsonExplorer:
    """Класс для навигации, анализа и модификации вложенных JSON-структур."""

    def __init__(self, data: Any):
        self._data = data

    # ------------------------------------------------------------------
    #  Свойство для доступа к данным
    # ------------------------------------------------------------------
    @property
    def data(self) -> Any:
        return self._data

    @data.setter
    def data(self, value: Any):
        self._data = value

    # ==================================================================
    #  1. АНАЛИЗ СТРУКТУРЫ
    # ==================================================================

    def describe(self, data: Any = None, prefix: str = "", max_depth: int = 0) -> list[str]:
        """Возвращает описание структуры: путь, тип и размер каждого элемента.

        Args:
            data: данные для анализа (по умолчанию self._data).
            prefix: текущий префикс пути (для рекурсии).
            max_depth: максимальная глубина (0 — без ограничений).

        Returns:
            Список строк вида "путь  ->  тип (подробности)".
        """
        if data is None:
            data = self._data
        lines: list[str] = []
        current_depth = prefix.count(".") + prefix.count("[")
        if max_depth and current_depth >= max_depth:
            lines.append(f"{prefix or 'root'}  ->  {type(data).__name__} (truncated)")
            return lines

        if isinstance(data, dict):
            label = prefix or "root"
            lines.append(f"{label}  ->  dict ({len(data)} keys)")
            for key in data:
                child_prefix = f"{prefix}.{key}" if prefix else str(key)
                lines.extend(self.describe(data[key], child_prefix, max_depth))
        elif isinstance(data, list):
            label = prefix or "root"
            lines.append(f"{label}  ->  list ({len(data)} items)")
            for i, item in enumerate(data):
                child_prefix = f"{prefix}[{i}]"
                lines.extend(self.describe(item, child_prefix, max_depth))
        else:
            type_name = type(data).__name__
            val_repr = repr(data)
            if len(val_repr) > 80:
                val_repr = val_repr[:77] + "..."
            lines.append(f"{prefix}  ->  {type_name}: {val_repr}")
        return lines

    def print_describe(self, max_depth: int = 0) -> None:
        """Печатает описание структуры в консоль."""
        for line in self.describe(max_depth=max_depth):
            print(line)

    def schema(self, data: Any = None) -> Any:
        """Возвращает «скелет» структуры — dict/list с типами вместо значений.

        Полезно для быстрого понимания формы данных.
        """
        if data is None:
            data = self._data
        if isinstance(data, dict):
            return {k: self.schema(v) for k, v in data.items()}
        elif isinstance(data, list):
            if not data:
                return ["<empty list>"]
            return [self.schema(data[0]), f"... ({len(data)} items)"]
        else:
            return f"<{type(data).__name__}>"

    def depth(self, data: Any = None) -> int:
        """Возвращает максимальную глубину вложенности."""
        if data is None:
            data = self._data
        if isinstance(data, dict):
            return 1 + max((self.depth(v) for v in data.values()), default=0)
        elif isinstance(data, list):
            return 1 + max((self.depth(v) for v in data), default=0)
        return 0

    def all_keys(self, data: Any = None) -> list[str]:
        """Возвращает отсортированный список всех уникальных ключей во вложенной структуре."""
        if data is None:
            data = self._data
        keys: set[str] = set()
        self._collect_keys(data, keys)
        return sorted(keys)

    def key_frequency(self, data: Any = None) -> dict[str, int]:
        """Считает сколько раз каждый ключ встречается в структуре."""
        if data is None:
            data = self._data
        counter: Counter = Counter()
        self._count_keys(data, counter)
        return dict(counter.most_common())

    def type_summary(self, data: Any = None) -> dict[str, int]:
        """Считает количество значений каждого типа в структуре."""
        if data is None:
            data = self._data
        counter: Counter = Counter()
        self._count_types(data, counter)
        return dict(counter.most_common())

    # ==================================================================
    #  2. ПОИСК ПУТЕЙ К КЛЮЧАМ И ЗНАЧЕНИЯМ
    # ==================================================================

    def find_key(self, key: str, data: Any = None, prefix: str = "") -> list[str]:
        """Находит все пути, где встречается указанный ключ.

        Args:
            key: имя ключа для поиска.

        Returns:
            Список путей вида "a.b.c" или "a[0].b".
        """
        if data is None:
            data = self._data
        results: list[str] = []
        if isinstance(data, dict):
            for k, v in data.items():
                current = f"{prefix}.{k}" if prefix else str(k)
                if k == key:
                    results.append(current)
                results.extend(self.find_key(key, v, current))
        elif isinstance(data, list):
            for i, item in enumerate(data):
                current = f"{prefix}[{i}]"
                results.extend(self.find_key(key, item, current))
        return results

    def find_value(self, value: Any, data: Any = None, prefix: str = "") -> list[str]:
        """Находит все пути, где встречается указанное значение.

        Сравнение по ==.
        """
        if data is None:
            data = self._data
        results: list[str] = []
        if isinstance(data, dict):
            for k, v in data.items():
                current = f"{prefix}.{k}" if prefix else str(k)
                if v == value:
                    results.append(current)
                results.extend(self.find_value(value, v, current))
        elif isinstance(data, list):
            for i, item in enumerate(data):
                current = f"{prefix}[{i}]"
                if item == value:
                    results.append(current)
                results.extend(self.find_value(value, item, current))
        return results

    def find_by_condition(self, predicate, data: Any = None, prefix: str = "") -> list[tuple[str, Any]]:
        """Находит все пути и значения, удовлетворяющие условию.

        Args:
            predicate: функция (key_or_index, value) -> bool.

        Returns:
            Список кортежей (путь, значение).
        """
        if data is None:
            data = self._data
        results: list[tuple[str, Any]] = []
        if isinstance(data, dict):
            for k, v in data.items():
                current = f"{prefix}.{k}" if prefix else str(k)
                if predicate(k, v):
                    results.append((current, v))
                results.extend(self.find_by_condition(predicate, v, current))
        elif isinstance(data, list):
            for i, item in enumerate(data):
                current = f"{prefix}[{i}]"
                if predicate(i, item):
                    results.append((current, item))
                results.extend(self.find_by_condition(predicate, item, current))
        return results

    # ==================================================================
    #  3. ИЗВЛЕЧЕНИЕ И МОДИФИКАЦИЯ ЗНАЧЕНИЙ
    # ==================================================================

    def get(self, path: str, default: Any = None) -> Any:
        """Извлекает значение по строковому пути.

        Формат пути: "key1.key2[0].key3"
        """
        keys = self._parse_path(path)
        obj = self._data
        for k in keys:
            try:
                if isinstance(k, int):
                    obj = obj[k]
                else:
                    obj = obj[k]
            except (KeyError, IndexError, TypeError):
                return default
        return obj

    def set(self, path: str, value: Any) -> bool:
        """Устанавливает значение по строковому пути.

        Возвращает True при успехе.
        """
        keys = self._parse_path(path)
        if not keys:
            return False
        obj = self._data
        for k in keys[:-1]:
            try:
                obj = obj[k]
            except (KeyError, IndexError, TypeError):
                return False
        try:
            obj[keys[-1]] = value
            return True
        except (KeyError, IndexError, TypeError):
            return False

    def set_by_key(self, key: str, new_value: Any) -> list[str]:
        """Находит ВСЕ вхождения ключа и заменяет их значения.

        Если вхождений больше одного, возвращает список путей
        и НЕ изменяет данные (для безопасности). Используйте
        set_by_key(key, value) после проверки, или force_set_by_key.

        Returns:
            Список изменённых путей. Если > 1 пути, ничего не меняется.
        """
        paths = self.find_key(key)
        if not paths:
            return []
        if len(paths) == 1:
            self.set(paths[0], new_value)
            return paths
        return paths

    def force_set_by_key(self, key: str, new_value: Any) -> list[str]:
        """Заменяет значение по ключу во ВСЕХ местах, где он встречается."""
        paths = self.find_key(key)
        for path in paths:
            self.set(path, new_value)
        return paths

    def delete(self, path: str) -> bool:
        """Удаляет элемент по пути."""
        keys = self._parse_path(path)
        if not keys:
            return False
        obj = self._data
        for k in keys[:-1]:
            try:
                obj = obj[k]
            except (KeyError, IndexError, TypeError):
                return False
        try:
            if isinstance(obj, dict):
                del obj[keys[-1]]
            elif isinstance(obj, list) and isinstance(keys[-1], int):
                obj.pop(keys[-1])
            else:
                return False
            return True
        except (KeyError, IndexError):
            return False

    # ==================================================================
    #  4. СРАВНЕНИЕ НЕСКОЛЬКИХ СТРУКТУР
    # ==================================================================

    @staticmethod
    def common_keys(*explorers: "JsonExplorer") -> set[str]:
        """Находит ключи, общие для всех переданных структур."""
        if not explorers:
            return set()
        sets = [set(e.all_keys()) for e in explorers]
        return sets[0].intersection(*sets[1:])

    @staticmethod
    def unique_keys(*explorers: "JsonExplorer") -> dict[int, set[str]]:
        """Для каждой структуры показывает ключи, уникальные только для неё.

        Returns:
            dict вида {индекс_структуры: set(уникальных ключей)}.
        """
        if not explorers:
            return {}
        all_sets = [set(e.all_keys()) for e in explorers]
        union_others = {}
        for i in range(len(all_sets)):
            others = set()
            for j, s in enumerate(all_sets):
                if j != i:
                    others |= s
            union_others[i] = all_sets[i] - others
        return union_others

    @staticmethod
    def diff_structure(a: "JsonExplorer", b: "JsonExplorer") -> dict[str, Any]:
        """Сравнивает два объекта и возвращает отличия.

        Returns:
            dict с ключами:
              - only_in_a: ключи только в первом
              - only_in_b: ключи только во втором
              - common: общие ключи
              - type_mismatches: ключи, где типы отличаются {key: (type_a, type_b)}
              - value_diffs: ключи, где значения (листья) отличаются {path: (val_a, val_b)}
        """
        keys_a = set(a.all_keys())
        keys_b = set(b.all_keys())

        result = {
            "only_in_a": sorted(keys_a - keys_b),
            "only_in_b": sorted(keys_b - keys_a),
            "common": sorted(keys_a & keys_b),
            "type_mismatches": {},
            "value_diffs": {},
        }

        for key in result["common"]:
            paths_a = a.find_key(key)
            paths_b = b.find_key(key)
            for pa in paths_a:
                val_a = a.get(pa)
                val_b = b.get(pa)
                if val_b is None and pa not in paths_b:
                    continue
                ta = type(val_a).__name__
                tb = type(val_b).__name__
                if ta != tb:
                    result["type_mismatches"][pa] = (ta, tb)
                elif val_a != val_b and not isinstance(val_a, (dict, list)):
                    result["value_diffs"][pa] = (val_a, val_b)

        return result

    # ==================================================================
    #  5. ЭКСПОРТ (CSV, файл, консоль)
    # ==================================================================

    def flatten(self, data: Any = None, prefix: str = "", sep: str = ".") -> dict[str, Any]:
        """Выравнивает вложенную структуру в плоский dict.

        Ключи — пути вида "a.b[0].c".
        """
        if data is None:
            data = self._data
        flat: dict[str, Any] = {}
        if isinstance(data, dict):
            for k, v in data.items():
                new_key = f"{prefix}{sep}{k}" if prefix else str(k)
                flat.update(self.flatten(v, new_key, sep))
        elif isinstance(data, list):
            for i, item in enumerate(data):
                new_key = f"{prefix}[{i}]"
                flat.update(self.flatten(item, new_key, sep))
        else:
            flat[prefix] = data
        return flat

    def to_csv(self, file_path: str | None = None) -> str:
        """Экспортирует плоскую структуру в CSV (path, value, type).

        Args:
            file_path: путь для сохранения. Если None — возвращает строку.

        Returns:
            CSV-строка.
        """
        flat = self.flatten()
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["path", "value", "type"])
        for path, value in flat.items():
            writer.writerow([path, value, type(value).__name__])

        csv_text = output.getvalue()
        if file_path:
            with open(file_path, "w", encoding="utf-8", newline="") as f:
                f.write(csv_text)
        return csv_text

    def to_json(self, file_path: str | None = None, indent: int = 2) -> str:
        """Экспортирует данные в JSON.

        Args:
            file_path: путь для сохранения. Если None — возвращает строку.

        Returns:
            JSON-строка.
        """
        text = json.dumps(self._data, ensure_ascii=False, indent=indent)
        if file_path:
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(text)
        return text

    def print_paths(self, key: str | None = None, value: Any = None) -> None:
        """Печатает все пути к ключу и/или значению."""
        if key is not None:
            paths = self.find_key(key)
            print(f"Paths for key '{key}' ({len(paths)}):")
            for p in paths:
                val = self.get(p)
                print(f"  {p}  ->  {repr(val)}")
        if value is not None:
            paths = self.find_value(value)
            print(f"Paths for value {repr(value)} ({len(paths)}):")
            for p in paths:
                print(f"  {p}")

    @staticmethod
    def print_diff(diff: dict[str, Any]) -> None:
        """Красиво выводит результат diff_structure."""
        if diff["only_in_a"]:
            print(f"Only in A ({len(diff['only_in_a'])}):")
            for k in diff["only_in_a"]:
                print(f"  - {k}")
        if diff["only_in_b"]:
            print(f"Only in B ({len(diff['only_in_b'])}):")
            for k in diff["only_in_b"]:
                print(f"  + {k}")
        if diff["type_mismatches"]:
            print(f"Type mismatches ({len(diff['type_mismatches'])}):")
            for path, (ta, tb) in diff["type_mismatches"].items():
                print(f"  {path}: {ta} vs {tb}")
        if diff["value_diffs"]:
            print(f"Value differences ({len(diff['value_diffs'])}):")
            for path, (va, vb) in diff["value_diffs"].items():
                print(f"  {path}: {repr(va)} -> {repr(vb)}")
        if not any([diff["only_in_a"], diff["only_in_b"],
                     diff["type_mismatches"], diff["value_diffs"]]):
            print("Structures are identical.")

    # ==================================================================
    #  6. ДОПОЛНИТЕЛЬНЫЕ ПОЛЕЗНЫЕ ФУНКЦИИ
    # ==================================================================

    def copy(self) -> "JsonExplorer":
        """Возвращает глубокую копию."""
        return JsonExplorer(copy.deepcopy(self._data))

    def extract_subtree(self, path: str) -> "JsonExplorer":
        """Извлекает поддерево по пути и оборачивает в новый JsonExplorer."""
        return JsonExplorer(copy.deepcopy(self.get(path)))

    def collect_values(self, key: str) -> list[Any]:
        """Собирает все значения для указанного ключа по всей структуре."""
        paths = self.find_key(key)
        return [self.get(p) for p in paths]

    def filter_list(self, path: str, predicate) -> list[Any]:
        """Фильтрует список по указанному пути.

        Args:
            path: путь к списку в структуре.
            predicate: функция (item) -> bool.

        Returns:
            Отфильтрованные элементы.
        """
        lst = self.get(path)
        if not isinstance(lst, list):
            return []
        return [item for item in lst if predicate(item)]

    def search_text(self, text: str, case_sensitive: bool = False) -> list[tuple[str, Any]]:
        """Ищет текст среди всех строковых значений.

        Returns:
            Список (путь, значение) где текст найден.
        """
        flat = self.flatten()
        results = []
        for path, value in flat.items():
            if isinstance(value, str):
                hay = value if case_sensitive else value.lower()
                needle = text if case_sensitive else text.lower()
                if needle in hay:
                    results.append((path, value))
        return results

    def size(self) -> dict[str, int]:
        """Возвращает статистику по размеру структуры."""
        flat = self.flatten()
        return {
            "total_leaves": len(flat),
            "total_keys": len(self.all_keys()),
            "max_depth": self.depth(),
        }

    @classmethod
    def from_file(cls, file_path: str) -> "JsonExplorer":
        """Создаёт JsonExplorer из JSON-файла."""
        with open(file_path, "r", encoding="utf-8") as f:
            return cls(json.load(f))

    @classmethod
    def from_string(cls, json_string: str) -> "JsonExplorer":
        """Создаёт JsonExplorer из JSON-строки."""
        return cls(json.loads(json_string))

    def __repr__(self) -> str:
        tp = type(self._data).__name__
        if isinstance(self._data, dict):
            return f"JsonExplorer(dict, {len(self._data)} keys, depth={self.depth()})"
        elif isinstance(self._data, list):
            return f"JsonExplorer(list, {len(self._data)} items, depth={self.depth()})"
        return f"JsonExplorer({tp})"

    # ------------------------------------------------------------------
    #  Приватные вспомогательные методы
    # ------------------------------------------------------------------

    @staticmethod
    def _parse_path(path: str) -> list:
        """Парсит строковый путь "a.b[0].c" в список ключей/индексов."""
        import re
        tokens = re.split(r'\.(?![^\[]*\])', path)
        keys: list = []
        for token in tokens:
            parts = re.split(r'(\[\d+\])', token)
            for part in parts:
                if not part:
                    continue
                m = re.match(r'^\[(\d+)\]$', part)
                if m:
                    keys.append(int(m.group(1)))
                else:
                    keys.append(part)
        return keys

    def _collect_keys(self, data: Any, keys: set):
        if isinstance(data, dict):
            for k, v in data.items():
                keys.add(k)
                self._collect_keys(v, keys)
        elif isinstance(data, list):
            for item in data:
                self._collect_keys(item, keys)

    def _count_keys(self, data: Any, counter: Counter):
        if isinstance(data, dict):
            for k, v in data.items():
                counter[k] += 1
                self._count_keys(v, counter)
        elif isinstance(data, list):
            for item in data:
                self._count_keys(item, counter)

    def _count_types(self, data: Any, counter: Counter):
        if isinstance(data, dict):
            counter["dict"] += 1
            for v in data.values():
                self._count_types(v, counter)
        elif isinstance(data, list):
            counter["list"] += 1
            for item in data:
                self._count_types(item, counter)
        else:
            counter[type(data).__name__] += 1


# ======================================================================
#  Пример использования
# ======================================================================
if __name__ == "__main__":
    sample = {
        "users": [
            {
                "id": 1,
                "name": "Alice",
                "address": {"city": "Moscow", "zip": "101000"},
                "tags": ["admin", "active"],
            },
            {
                "id": 2,
                "name": "Bob",
                "address": {"city": "London", "zip": "EC1A"},
                "tags": ["user"],
            },
        ],
        "meta": {"total": 2, "page": 1},
    }

    sample2 = {
        "users": [
            {
                "id": 10,
                "name": "Charlie",
                "address": {"city": "Berlin", "country": "DE"},
                "role": "editor",
            }
        ],
        "meta": {"total": 1, "version": "2.0"},
    }

    explorer = JsonExplorer(sample)
    explorer2 = JsonExplorer(sample2)

    print("=" * 60)
    print("ОПИСАНИЕ СТРУКТУРЫ:")
    print("=" * 60)
    explorer.print_describe()

    print("\n" + "=" * 60)
    print("СХЕМА:")
    print("=" * 60)
    print(json.dumps(explorer.schema(), ensure_ascii=False, indent=2))

    print("\n" + "=" * 60)
    print("ПОИСК КЛЮЧА 'city':")
    print("=" * 60)
    explorer.print_paths(key="city")

    print("\n" + "=" * 60)
    print("ПОИСК ЗНАЧЕНИЯ 'Bob':")
    print("=" * 60)
    explorer.print_paths(value="Bob")

    print("\n" + "=" * 60)
    print("ИЗВЛЕЧЕНИЕ ПО ПУТИ 'users[1].address':")
    print("=" * 60)
    print(explorer.get("users[1].address"))

    print("\n" + "=" * 60)
    print("ИЗМЕНЕНИЕ ЗНАЧЕНИЯ city -> Saint-Petersburg (по ключу):")
    print("=" * 60)
    result = explorer.set_by_key("city", "Saint-Petersburg")
    if len(result) > 1:
        print(f"Найдено {len(result)} вхождений, изменение не применено:")
        for path in result:
            print(f"  {path}  ->  {explorer.get(path)}")
        print("Используйте force_set_by_key() или set() с конкретным путём.")
    else:
        print(f"Изменено: {result}")

    print("\n" + "=" * 60)
    print("СРАВНЕНИЕ ДВУХ СТРУКТУР:")
    print("=" * 60)
    diff = JsonExplorer.diff_structure(explorer, explorer2)
    JsonExplorer.print_diff(diff)

    print("\n" + "=" * 60)
    print("ОБЩИЕ КЛЮЧИ:")
    print("=" * 60)
    print(JsonExplorer.common_keys(explorer, explorer2))

    print("\n" + "=" * 60)
    print("ТЕКСТОВЫЙ ПОИСК 'alice':")
    print("=" * 60)
    print(explorer.search_text("alice"))

    print("\n" + "=" * 60)
    print("СТАТИСТИКА:")
    print("=" * 60)
    print(explorer.size())
    print(f"Частота ключей: {explorer.key_frequency()}")
    print(f"Типы значений: {explorer.type_summary()}")

    print("\n" + "=" * 60)
    print("CSV (первые 5 строк):")
    print("=" * 60)
    csv_output = explorer.to_csv()
    for line in csv_output.splitlines()[:6]:
        print(line)

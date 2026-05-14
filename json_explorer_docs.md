# JsonExplorer — Документация

Класс для навигации, анализа и модификации вложенных JSON-структур,
которые возвращаются при парсинге сайтов или работе с API.

---

## Содержание

1. [Создание объекта](#создание-объекта)
2. [Анализ структуры](#1-анализ-структуры)
3. [Поиск путей](#2-поиск-путей-к-ключам-и-значениям)
4. [Извлечение и изменение](#3-извлечение-и-изменение-значений)
5. [Сравнение структур](#4-сравнение-нескольких-структур)
6. [Экспорт](#5-экспорт)
7. [Дополнительные функции](#6-дополнительные-функции)
8. [Формат путей](#формат-путей)

---

## Тестовые данные (используются во всех примерах)

```python
from json_explorer import JsonExplorer

data = {
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

data2 = {
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

ex  = JsonExplorer(data)
ex2 = JsonExplorer(data2)
```

---

## Создание объекта

| Способ | Описание |
|---|---|
| `JsonExplorer(dict_or_list)` | Из уже готового Python-объекта |
| `JsonExplorer.from_string(json_str)` | Из JSON-строки |
| `JsonExplorer.from_file("path.json")` | Из JSON-файла |

```python
# Из Python-объекта
ex = JsonExplorer({"key": "value"})

# Из строки (например, из requests.text или open().read())
ex = JsonExplorer.from_string('{"key": "value"}')

# Из файла
ex = JsonExplorer.from_file("response.json")

# Доступ к исходным данным
raw = ex.data           # чтение
ex.data = new_dict      # замена всей структуры

# Представление объекта
print(ex)
# JsonExplorer(dict, 2 keys, depth=4)
```

---

## 1. Анализ структуры

### `describe(max_depth=0)` / `print_describe(max_depth=0)`

Показывает полное дерево: путь, тип и значение каждого элемента.
`max_depth=0` — без ограничений глубины.

```python
ex.print_describe()
```
```
root  ->  dict (2 keys)
users  ->  list (2 items)
users[0]  ->  dict (4 keys)
users[0].id  ->  int: 1
users[0].name  ->  str: 'Alice'
users[0].address  ->  dict (2 keys)
users[0].address.city  ->  str: 'Moscow'
users[0].address.zip  ->  str: '101000'
users[0].tags  ->  list (2 items)
users[0].tags[0]  ->  str: 'admin'
users[0].tags[1]  ->  str: 'active'
...
meta  ->  dict (2 keys)
meta.total  ->  int: 2
meta.page  ->  int: 1
```

```python
# Ограничение глубины — только первые 2 уровня
ex.print_describe(max_depth=2)
```
```
root  ->  dict (2 keys)
users  ->  list (2 items)
users[0]  ->  dict (truncated)
users[1]  ->  dict (truncated)
meta  ->  dict (2 keys)
meta.total  ->  int (truncated)
meta.page  ->  int (truncated)
```

---

### `schema()`

Возвращает «скелет» структуры — типы вместо значений. Полезно для
быстрого понимания формы ответа API.

```python
import json
print(json.dumps(ex.schema(), ensure_ascii=False, indent=2))
```
```json
{
  "users": [
    {
      "id": "<int>",
      "name": "<str>",
      "address": {
        "city": "<str>",
        "zip": "<str>"
      },
      "tags": ["<str>", "... (2 items)"]
    },
    "... (2 items)"
  ],
  "meta": {
    "total": "<int>",
    "page": "<int>"
  }
}
```

---

### `depth()`

Возвращает максимальную глубину вложенности.

```python
ex.depth()   # 4
```

---

### `all_keys()`

Список всех уникальных ключей во всей структуре (отсортированный).

```python
ex.all_keys()
# ['address', 'city', 'id', 'meta', 'name', 'page', 'tags', 'total', 'users', 'zip']
```

---

### `key_frequency()`

Сколько раз каждый ключ встречается в структуре. Удобно для анализа
повторяющихся блоков (например, список товаров, где у каждого есть `price`).

```python
ex.key_frequency()
# {'id': 2, 'name': 2, 'address': 2, 'city': 2, 'zip': 2, 'tags': 2,
#  'users': 1, 'meta': 1, 'total': 1, 'page': 1}
```

---

### `type_summary()`

Количество значений каждого типа во всей структуре.

```python
ex.type_summary()
# {'str': 9, 'dict': 6, 'int': 4, 'list': 3}
```

---

### `size()`

Общая статистика: количество листовых значений, уникальных ключей, глубина.

```python
ex.size()
# {'total_leaves': 13, 'total_keys': 10, 'max_depth': 4}
```

---

## 2. Поиск путей к ключам и значениям

### `find_key(key)` / `print_paths(key=...)`

Находит все пути, где встречается указанный ключ.

```python
ex.find_key("city")
# ['users[0].address.city', 'users[1].address.city']

# С печатью значений:
ex.print_paths(key="city")
```
```
Paths for key 'city' (2):
  users[0].address.city  ->  'Moscow'
  users[1].address.city  ->  'London'
```

---

### `find_value(value)` / `print_paths(value=...)`

Находит все пути, где встречается указанное значение (сравнение по `==`).

```python
ex.find_value("Bob")
# ['users[1].name']

ex.print_paths(value=2)
```
```
Paths for value 2 (2):
  users[1].id
  meta.total
```

---

### `print_paths(key=..., value=...)`

Можно передать оба аргумента одновременно.

```python
ex.print_paths(key="id", value=1)
```
```
Paths for key 'id' (2):
  users[0].id  ->  1
  users[1].id  ->  2
Paths for value 1 (1):
  users[0].id
```

---

### `find_by_condition(predicate)`

Поиск по произвольному условию. Функция-предикат принимает `(key_or_index, value)`.

```python
# Найти все элементы, где значение — строка длиннее 4 символов
results = ex.find_by_condition(lambda k, v: isinstance(v, str) and len(v) > 4)
for path, val in results:
    print(f"{path}: {val!r}")
```
```
users[0].name: 'Alice'
users[0].address.city: 'Moscow'
users[0].address.zip: '101000'
users[0].tags[0]: 'admin'
users[0].tags[1]: 'active'
users[1].name: 'Bob'   # <- 3 символа, не попадает
users[1].address.city: 'London'
users[1].address.zip: 'EC1A'
```

```python
# Найти все числовые значения больше 1
results = ex.find_by_condition(lambda k, v: isinstance(v, int) and v > 1)
# [('users[1].id', 2), ('meta.total', 2)]
```

---

### `search_text(text, case_sensitive=False)`

Поиск подстроки среди всех строковых значений. По умолчанию регистронезависимый.

```python
ex.search_text("ali")
# [('users[0].name', 'Alice')]

ex.search_text("EC", case_sensitive=True)
# [('users[1].address.zip', 'EC1A')]
```

---

## 3. Извлечение и изменение значений

### `get(path, default=None)`

Извлекает значение по строковому пути. Возвращает `default` если путь не существует.

```python
ex.get("users[0].name")              # 'Alice'
ex.get("users[1].address")           # {'city': 'London', 'zip': 'EC1A'}
ex.get("users[0].tags[1]")           # 'active'
ex.get("meta.total")                  # 2
ex.get("meta.missing", "N/A")        # 'N/A'
```

---

### `set(path, value)`

Изменяет значение по конкретному пути. Возвращает `True` при успехе.

```python
ex.set("users[0].name", "Алиса")
ex.get("users[0].name")   # 'Алиса'

ex.set("users[1].address.city", "Берлин")
ex.set("meta.page", 2)
```

---

### `set_by_key(key, new_value)`

Безопасная замена по имени ключа:
- Если ключ встречается **один раз** — меняет и возвращает `[path]`.
- Если встречается **несколько раз** — ничего не меняет, возвращает все пути
  (чтобы вы могли выбрать нужный и использовать `set()`).

```python
# Безопасный случай — ключ уникален
result = ex.set_by_key("page", 99)
# result = ['meta.page'] — изменено

# Неоднозначный случай — несколько вхождений
result = ex.set_by_key("city", "Токио")
# result = ['users[0].address.city', 'users[1].address.city']
# Данные НЕ изменены! Выберите нужный путь:
ex.set(result[0], "Токио")   # только первый пользователь
```

---

### `force_set_by_key(key, new_value)`

Заменяет значение по ключу **во всех местах** без предупреждений.

```python
changed = ex.force_set_by_key("city", "Токио")
# changed = ['users[0].address.city', 'users[1].address.city']
# Оба города теперь 'Токио'
```

---

### `collect_values(key)`

Собирает все значения ключа по всей структуре в один список.

```python
ex.collect_values("city")   # ['Moscow', 'London']
ex.collect_values("id")     # [1, 2]
ex.collect_values("tags")   # [['admin', 'active'], ['user']]
```

---

### `delete(path)`

Удаляет элемент по пути. Возвращает `True` при успехе.

```python
ex.delete("meta.page")
ex.get("meta.page")       # None

ex.delete("users[0].tags[0]")   # удалить первый тег у первого пользователя
```

---

## 4. Сравнение нескольких структур

### `JsonExplorer.common_keys(*explorers)`

Ключи, присутствующие во **всех** переданных структурах.

```python
JsonExplorer.common_keys(ex, ex2)
# {'id', 'name', 'address', 'city', 'users', 'meta', 'total'}
```

---

### `JsonExplorer.unique_keys(*explorers)`

Для каждой структуры — ключи, которые есть **только в ней**.

```python
uniq = JsonExplorer.unique_keys(ex, ex2)
uniq[0]   # {'zip', 'tags', 'page'}       — только в ex
uniq[1]   # {'country', 'role', 'version'} — только в ex2
```

---

### `JsonExplorer.diff_structure(a, b)` / `JsonExplorer.print_diff(diff)`

Детальное сравнение двух структур.

```python
diff = JsonExplorer.diff_structure(ex, ex2)
JsonExplorer.print_diff(diff)
```
```
Only in A (3):
  - page
  - tags
  - zip
Only in B (3):
  + country
  + role
  + version
Value differences (4):
  users[0].address.city: 'Moscow' -> 'Berlin'
  users[0].id: 1 -> 10
  users[0].name: 'Alice' -> 'Charlie'
  meta.total: 2 -> 1
```

Сырой результат `diff_structure` — обычный `dict`:

```python
diff = JsonExplorer.diff_structure(ex, ex2)
diff["only_in_a"]        # ['page', 'tags', 'zip']
diff["only_in_b"]        # ['country', 'role', 'version']
diff["common"]           # ['address', 'city', 'id', ...]
diff["type_mismatches"]  # {} — нет несовпадений типов
diff["value_diffs"]      # {'users[0].id': (1, 10), ...}
```

---

## 5. Экспорт

### `flatten(sep=".")`

Разворачивает вложенную структуру в плоский `dict`. Ключи — пути.

```python
flat = ex.flatten()
# {
#   'users[0].id': 1,
#   'users[0].name': 'Alice',
#   'users[0].address.city': 'Moscow',
#   'users[0].address.zip': '101000',
#   'users[0].tags[0]': 'admin',
#   ...
# }
```

---

### `to_csv(file_path=None)`

Экспортирует плоскую структуру в CSV с колонками `path, value, type`.
Если `file_path` не указан — возвращает строку.

```python
# В консоль
print(ex.to_csv())

# В файл
ex.to_csv("output.csv")
```
```
path,value,type
users[0].id,1,int
users[0].name,Alice,str
users[0].address.city,Moscow,str
users[0].address.zip,101000,str
users[0].tags[0],admin,str
users[0].tags[1],active,str
users[1].id,2,int
...
meta.total,2,int
meta.page,1,int
```

---

### `to_json(file_path=None, indent=2)`

Экспортирует данные в JSON-строку или файл.

```python
print(ex.to_json())          # в консоль
ex.to_json("result.json")    # в файл
```

---

## 6. Дополнительные функции

### `extract_subtree(path)`

Извлекает поддерево по пути и возвращает **новый** `JsonExplorer`.
Исходный объект не изменяется (глубокая копия).

```python
sub = ex.extract_subtree("users[0]")
print(sub)
# JsonExplorer(dict, 4 keys, depth=2)

sub.print_describe()
# root  ->  dict (4 keys)
# id  ->  int: 1
# name  ->  str: 'Alice'
# address  ->  dict (2 keys)
# address.city  ->  str: 'Moscow'
# ...
```

---

### `filter_list(path, predicate)`

Фильтрует список по пути. Удобно для отбора нужных элементов из массивов.

```python
# Только пользователи с id > 1
ex.filter_list("users", lambda u: u["id"] > 1)
# [{'id': 2, 'name': 'Bob', ...}]

# Только пользователи с тегом 'admin'
ex.filter_list("users", lambda u: "admin" in u.get("tags", []))
# [{'id': 1, 'name': 'Alice', ...}]
```

---

### `copy()`

Возвращает полную независимую копию объекта.

```python
backup = ex.copy()
ex.set("meta.page", 999)
backup.get("meta.page")   # 1 — копия не изменилась
```

---

### `__repr__`

Краткая информация об объекте при выводе.

```python
print(ex)
# JsonExplorer(dict, 2 keys, depth=4)

print(JsonExplorer([1, 2, 3]))
# JsonExplorer(list, 3 items, depth=1)
```

---

## Формат путей

Все методы `get`, `set`, `delete`, `extract_subtree` используют единый
строковый формат пути:

| Ситуация | Пример пути |
|---|---|
| Вложенный ключ | `"meta.total"` |
| Элемент списка | `"users[0]"` |
| Комбинация | `"users[1].address.city"` |
| Список в списке | `"users[0].tags[1]"` |

```python
ex.get("users[0].address.city")   # 'Moscow'
ex.get("users[1].tags[0]")        # 'user'
ex.set("users[0].id", 100)
ex.delete("users[1].address.zip")
```

> **Примечание.** Ключи с точками в именах (`"key.with.dot"`) не поддерживаются
> в строковом формате пути. В таких редких случаях используйте прямой доступ
> через `ex.data["key.with.dot"]`.

---

## Быстрая шпаргалка

```python
from json_explorer import JsonExplorer

ex = JsonExplorer.from_file("data.json")   # загрузить

# --- Изучить ---
ex.print_describe()                # дерево структуры
ex.schema()                        # скелет типов
ex.depth()                         # глубина
ex.all_keys()                      # все ключи
ex.key_frequency()                 # частота ключей
ex.type_summary()                  # типы значений
ex.size()                          # статистика

# --- Найти ---
ex.find_key("price")               # пути к ключу
ex.find_value(None)                # пути к значению
ex.find_by_condition(lambda k, v: isinstance(v, float))  # по условию
ex.search_text("error")            # текстовый поиск

# --- Получить/Изменить ---
ex.get("items[0].price")           # извлечь по пути
ex.set("items[0].price", 9.99)     # изменить по пути
ex.set_by_key("status", "active")  # безопасная замена
ex.force_set_by_key("active", True)  # замена везде
ex.collect_values("id")            # все значения ключа
ex.delete("meta.debug")            # удалить

# --- Сравнить ---
JsonExplorer.common_keys(ex, ex2)
JsonExplorer.unique_keys(ex, ex2)
JsonExplorer.print_diff(JsonExplorer.diff_structure(ex, ex2))

# --- Экспорт ---
ex.to_csv("out.csv")               # в CSV
ex.to_json("out.json")             # в JSON
flat = ex.flatten()                # плоский dict

# --- Прочее ---
sub = ex.extract_subtree("items[0]")          # поддерево
filtered = ex.filter_list("items", lambda i: i["price"] > 10)
backup = ex.copy()                            # копия
```

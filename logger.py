import logging
import json
import inspect
from datetime import datetime


class LoggerSaveJSL:
    '''
    Вызов записи объекта класса -
        logger.info("Просто лог", extra={'params_name': 'ManualLog', 'params_value': 100})
        При вызове логгера  в экстре для save_python_logs обязательных 2 параметра:
        params_name и params_value
    '''

    dict_log_lvl = {
        'DEBUG': logging.DEBUG,  # 10
        'INFO': logging.INFO,  # 20
        'WARNING': logging.WARNING,  # 30
        'ERROR': logging.ERROR,  # 40
        'CRITICAL': logging.CRITICAL,  # 50
    }

    params = {
        'str_funcs': 'Запуск функции',
        'end_funcs': 'окончание работы функции',
        'start_class': 'Сформирован объект класса',
        'str_obj': 'определен объект',
        'chan_mod': 'Изменен объект'
    }

    def __init__(self, Log_LVL):
        self.Log_LVL = self.__chec_lvl(Log_LVL)

    @staticmethod
    def __chec_lvl(lvl):
        if isinstance(lvl, str) and LoggerSaveJSL.dict_log_lvl.get(lvl.upper()) is not None:
            return lvl.upper()
        else:
            raise ValueError(f'''Указанный вами уровень {lvl} не существует!
Введите 1 из предложенных: DEBUG, INFO, WARNING, ERROR, CRITICAL
''')

    def __process_value(self, val):
        """Вспомогательный метод для приведения сложных объектов к читаемому виду"""
        if val is None:
            return 'None'

        # Для функций: имя + параметры
        if callable(val):
            name = getattr(val, '__name__', '<anonymous>')
            try:
                sig = inspect.signature(val)
                params_sig = {n: str(p) for n, p in sig.parameters.items()}
                return f"{type(val)}: {name} (params: {params_sig})"
            except (ValueError, TypeError):
                return f"{type(val)}: {name}"

        # Для коллекций: repr с лимитом
        if isinstance(val, (list, dict, set, tuple)):
            if len(val) > 10:
                items = list(val)[:10]
                return f"{repr(items)[:-1]}, ...]"
            return repr(val)

        # Для объектов: имя класса
        if hasattr(val, '__dict__') and not isinstance(val, str):
            return f"obj: {val.__class__.__name__}"

        return str(val)

    def __format_python_json(self, record):
        """Форматирование записи в JSON строку"""
        log_data = {
            'timestamp': datetime.fromtimestamp(record.created).isoformat(),
            'level': record.levelname,
            'message': record.getMessage(),
            'params_name': self.__process_value(getattr(record, 'params_name', 'unknown')),
            'params_value': self.__process_value(getattr(record, 'params_value', 'unknown')),
        }
        return json.dumps(log_data, ensure_ascii=False) + '\n'

    def __format_python_console(self, record):
        """Форматирование записи для вывода в консоль"""
        dt = datetime.fromtimestamp(record.created).strftime('%Y-%m-%d %H:%M:%S')
        p_name = self.__process_value(getattr(record, 'params_name', 'default'))
        return f"{dt} - {record.levelname} - {record.getMessage()} - {p_name}"

    def save_python_logs(self, file_name, lvl_file_handler='DEBUG', lvl_consol_handler='WARNING'):
        # ____Проверяю уровни на корректность____
        lvl_file_handler = self.__chec_lvl(lvl_file_handler)
        lvl_consol_handler = self.__chec_lvl(lvl_consol_handler)

        # ____Создаю логгер и объявляю уровень записи____
        logger = logging.getLogger('my_logger')
        logger.setLevel(self.dict_log_lvl[self.Log_LVL])

        if not logger.handlers:
            # ____Создаю хендлеры для консоли и для файла____
            file_handler = logging.FileHandler(filename=file_name, mode='a', encoding='utf-8')
            consol_handler = logging.StreamHandler()

            # ____Объявляю уровни записей хендлерров____
            file_handler.setLevel(self.dict_log_lvl[lvl_file_handler])
            consol_handler.setLevel(self.dict_log_lvl[lvl_consol_handler])

            # ____Прикрепляю к хендлеррам форматтеры____
            # Мы используем метод подмены функции format у стандартного Formatter
            f_formatter = logging.Formatter()
            f_formatter.format = self.__format_python_json
            file_handler.setFormatter(f_formatter)

            c_formatter = logging.Formatter()
            c_formatter.format = self.__format_python_console
            consol_handler.setFormatter(c_formatter)

            # ____Прикрепляю Хендлерры к логгеру____
            logger.addHandler(file_handler)
            logger.addHandler(consol_handler)

        return logger

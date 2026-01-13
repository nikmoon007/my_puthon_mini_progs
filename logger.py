import logging
import json
import inspect
from datetime import datetime
import atexit
import sys
import traceback


class LoggerSaveJSL:
    '''
    Вызов записи объекта класса -
        logger.info("Просто лог", extra={'params_name': 'ManualLog', 'params_value': 100})
        При вызове логгера в экстре для save_python_logs обязательных 2 параметра:
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
        'chan_mod': 'Изменен объект',
        'start_https': 'отправка сетевого запроса'
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

    def __format_http_json(self, record):
        """Отдельная функция для формирования лога для HTTP запросов"""
        log_data = {
            'timestamp': datetime.fromtimestamp(record.created).isoformat(),
            'level': record.levelname,
            'message': record.getMessage(),
            'status_code': getattr(record, 'status_code', 'unknown'),
            'headers' : getattr(record, 'headers', 'unknown'),
            'url' : getattr(record, 'url', 'unknown'),
            'request' : getattr(record, 'request', 'unknown'),
            'cookies' : self.__process_value(getattr(record, 'cookies', 'unknown')),
            'elapsed' : getattr(record, 'elapsed', 'unknown'),
            'result' : self.__process_value(getattr(record, 'result', 'unknown')),
        }
        return json.dumps(log_data, ensure_ascii=False) + '\n'

    def __format_http_console(self, record):
        """Форматирование записи для вывода в консоль"""
        dt = datetime.fromtimestamp(record.created).strftime('%Y-%m-%d %H:%M:%S')
        s_code = getattr(record, 'status_code', 'default')
        eled = getattr(record, 'elapsed', 'unknown')
        reqst = getattr(record, 'request', 'unknown')
        url = getattr(record, 'url', 'unknown')
        return f"{dt} - {record.levelname} - {record.getMessage()} \n{s_code} - {eled} - {reqst} - {url}"

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
        logger = logging.getLogger('my_logger_python')
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

    def save_http_logs(self, file_name, lvl_file_handler='DEBUG', lvl_consol_handler='WARNING'):
        # ____Проверяю уровни на корректность____
        lvl_file_handler = self.__chec_lvl(lvl_file_handler)
        lvl_consol_handler = self.__chec_lvl(lvl_consol_handler)

        # ____Создаю логгер и объявляю уровень записи____
        logger = logging.getLogger('my_logger_http')
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
            f_formatter.format = self.__format_http_json
            file_handler.setFormatter(f_formatter)

            c_formatter = logging.Formatter()
            c_formatter.format = self.__format_http_console
            consol_handler.setFormatter(c_formatter)

            # ____Прикрепляю Хендлерры к логгеру____
            logger.addHandler(file_handler)
            logger.addHandler(consol_handler)

        return logger

    def setup_exit_logging(self, logger, file_name=None, handle_errors=True):
        """
        Настраивает логирование состояния при завершении программы с помощью atexit.
        :param logger: Логгер, в который записывать (python или http).
        :param file_name: Опционально, отдельный файл для exit-логов (если не указан, использует существующий хендлер).
        :param handle_errors: Если True, также устанавливает sys.excepthook для логирования непойманных ошибок.
        """
        if file_name:
            # Добавляем отдельный хендлер для exit-логов, если указан
            exit_handler = logging.FileHandler(filename=file_name, mode='a', encoding='utf-8')
            # Используем подходящий форматтер в зависимости от типа логгера
            if logger.name == 'my_logger_python':
                f_formatter = logging.Formatter()
                f_formatter.format = self.__format_python_json
                exit_handler.setFormatter(f_formatter)
            else:  # Для HTTP
                f_formatter = logging.Formatter()
                f_formatter.format = self.__format_http_json
                exit_handler.setFormatter(f_formatter)
            logger.addHandler(exit_handler)

        if handle_errors:
            # Сохраняем оригинальный excepthook
            original_excepthook = sys.excepthook

            def my_excepthook(exc_type, exc_value, exc_traceback):
                # Извлекаем детали ошибки
                error_details = {
                    'type': exc_type.__name__,
                    'message': str(exc_value),
                    'full_traceback': ''.join(traceback.format_tb(exc_traceback)),
                    'last_line': traceback.format_tb(exc_traceback)[-1] if exc_traceback else 'N/A'
                    # Последняя строчка стека
                }

                # Логируем с extra для python-логгера
                if logger.name == 'my_logger_python':
                    logger.error("Непойманная ошибка!", extra={
                        'params_name': 'ErrorDetails',
                        'params_value': error_details
                    })
                else:  # Для HTTP просто сообщение
                    logger.error(f"Непойманная ошибка! Детали: {error_details}")

                # Вызываем оригинальный excepthook для консольного вывода
                original_excepthook(exc_type, exc_value, exc_traceback)

            # Устанавливаем хук
            sys.excepthook = my_excepthook

        def log_on_exit():
            global_vars = globals().copy()  # Копируем глобальные переменные
            # Убираем служебные, чтобы не засорять лог (опционально)
            global_vars.pop('__builtins__', None)
            global_vars.pop('__name__', None)
            global_vars.pop('__doc__', None)
            global_vars.pop('__package__', None)
            global_vars.pop('__loader__', None)
            global_vars.pop('__spec__', None)

            # Логируем с extra для совместимости с форматом
            if logger.name == 'my_logger_python':
                logger.info("Программа завершается.", extra={
                    'params_name': 'ExitState',
                    'params_value': global_vars
                })
            else:  # Для HTTP просто сообщение (без extra, т.к. формат отличается)
                logger.info(f"Программа завершается. Состояние: {global_vars}")

        # Регистрируем только раз
        atexit.register(log_on_exit)

"""
Примеры подключения логгера:
logg = LoggerSaveJSL('DEBUG')
logger = logg.save_python_logs('text_test.logs') # здесь может быть подключен метод для записи http лога - save_http_logs
logg.setup_exit_logging(logger) # вызывается 1 раз, ловит все ошибки и записывает их в файл
# Когда нужно вызвать лог для записи данных, просто пиши в каждую функцию/класс итд, чем больше таких вызовов, тем больше запишется
logger.info("Просто лог", extra={'params_name': 'ManualLog', 'params_value': 100})

__________________________________
Если нужно записать сетевой лог, то лучше делать это так:
logg = LoggerSaveJSL('DEBUG')
logger = logg.save_http_logs('text_test.logs')
logg.setup_exit_logging(logger)


res = requests.get('https://www.google.com/?hl=ru')
zn = res.__dict__
logger.debug("Сетевой лог", extra=\
        {
            'status_code': zn['status_code'],
            'headers': zn['headers'],
            'url' : zn['url'],
            'request' : zn['request'],
            'cookies' : zn['cookies'],
            'elapsed' : zn['elapsed'],
            'result' : res.text[:100] # может передавать и res.json
        }
                 )

"""

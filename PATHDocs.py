# С помощью этого класса я сохраняю разные текстовые объекты
class PATHDocs:
    path = os.getcwd()
    name_file = 'file'
    def __init__(self, ney_path=None, doc_format = 'txt', ney_name_file = None, status = 'a'):
        self.ney_patch = ney_path if ney_path is not None else self.path
        self.doc_format = doc_format
        self.ney_name_file = ney_name_file if ney_name_file is not None else self.name_file
        self.status = status

    def __craft_path(self):
        # Создаю путь к файлу, если его нет и возвращаю его
        user_path = os.path.join(self.ney_patch, (self.ney_name_file + f".{self.doc_format}"))
        if not os.path.exists(user_path):
            os.makedirs(self.ney_patch, exist_ok=True)
            self.status = 'w'

        return user_path

    @staticmethod
    def __is_correct_json(file):
        try:
            result = json.dumps(file)
            return True
        except:
            return False

    def craft_txt(self, file_data):
        user_path = self.__craft_path()
        with open(user_path, self.status, encoding='utf-8', newline='\n') as txt_file:
            if type(file_data) is list:
                new_file_data = [str(i) + '\n' for i in file_data]
                txt_file.writelines(new_file_data)
                txt_file.writelines('\n')
            else:
                txt_file.write(file_data)
                txt_file.write('\n')

    def craft_json(self, file_data):
        user_path = self.__craft_path()
        try:
            if not self.__is_correct_json(file_data):
                raise ValueError(f"❌ Указанное значение {file_data} не подходит для записи в json")

            data_list = []
            if self.status == 'a':
                with open(user_path, 'r', encoding='utf-8') as json_file_read:
                    try:
                        data_list = json.load(json_file_read)
                        if not isinstance(data_list, list):
                            data_list = []
                    except json.decoder.JSONDecodeError:
                        data_list = []

            data_list.append(file_data)
            with open(user_path, 'w', encoding='utf-8') as json_file_write:
                json.dump(data_list, json_file_write, ensure_ascii=False, indent=4)
        except ValueError as errors:
            print(errors)

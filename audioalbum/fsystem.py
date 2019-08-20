import os

ERROR_DELETE = 1
ERROR_RENAME = 2
ERROR_MOVE = 3


class FileSystemEdit:
    def __init__(self, files):
        self.files = files

    def delete_file(self, index):
        try:
            os.remove(self.files[index].path())
            return 0
        except Exception as e:
            print(e)
            return ERROR_DELETE

    def rename_file(self, index, name):
        filename = '{}.{}'.format(name, self.files[index].format)
        try:
            os.rename(
                self.files[index].path(),
                os.path.join(self.files[index].directory, filename))
            return 0
        except Exception as e:
            print(e)
            return ERROR_RENAME

    def move_file(self, index, directory):
        try:
            os.replace(
                self.files[index].path(),
                os.path.join(directory, self.files[index].file_name))
        except Exception as e:
            print(e)
            return ERROR_MOVE

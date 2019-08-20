import re
import os
import collections
import filecmp
import tinytag
from tinytag import TinyTag
import hashlib
import operator

FILENAME_RE = re.compile(r'(?P<name>.+)\.(?P<format>.+)$')


class AudioFile:
    def __init__(self, directory, file_name):
        self.directory = directory
        self.file_name = file_name
        match = FILENAME_RE.match(file_name)
        self.name = match.group('name')
        self.format = match.group('format')
        self.index = None
        self.hash = None
        try:
            self.meta = TinyTag.get(self.path())
        except tinytag.TinyTagException:
            self.meta = None
            print(self.path())
        except Exception:
            self.meta = None
            print(self.path())

    def path(self):
        return os.path.join(self.directory, self.file_name)


def create_regexp(formats):
    return re.compile(
        r'(?P<file_name>(.+)\.({}))$'.format(
            '|'.join(formats)))


def find_audio_files(directory, search_in_subdirs, formats):
    audio_re = create_regexp(formats)
    audio_files = []
    for root, dirs, files in os.walk(directory):
        for file in files:
            match = audio_re.match(file)
            if not match:
                continue
            audio = AudioFile(root, match.group('file_name'))
            if not audio.meta or audio.meta.duration == 0:
                continue
            audio_files.append(audio)
        if not search_in_subdirs:
            break
    sorted_files = sort(audio_files, 'name')
    return sorted_files


def find_name_in_files(name, files):
    reg = re.compile(r'{}'.format(name), re.IGNORECASE)
    result_list = []
    for file in files:
        match = reg.search(file.name)
        if not match:
            continue
        result_list.append(file)
    return result_list


def find_name_in_albums(name, albums):
    result_dict = {}
    for album_name, album in albums.items():
        result_list = find_name_in_files(name, album.album_items)
        if not result_list:
            continue
        result_dict[album_name] = result_list
    return result_dict


def find_all_repetitions(files):
    hashes_dict = create_nonunique_hashes_dict(files)
    repetitions = {}
    for hash in hashes_dict:
        checked_files = []
        for file in hashes_dict[hash]:
            if file in checked_files:
                continue
            checked_files.append(file)
            same_files = compare_and_find_files(
                file,
                [file for file in hashes_dict[hash]
                 if file not in checked_files])
            name = file.meta.title if file.meta and file.meta.title \
                else file.name
            repetitions[name] = *same_files, file
            checked_files += same_files
    return repetitions


def create_nonunique_hashes_dict(input_files):
    files = find_nonunique_sizes(input_files)
    count_hash(files)
    hash_counter = collections.Counter(file.hash for file in files)
    rep_files = [file for file in files if hash_counter[file.hash] > 1]
    hashes_dict = {hash: [] for hash in hash_counter if hash_counter[hash] > 1}
    for file in rep_files:
        hashes_dict[file.hash].append(file)
    return hashes_dict


def find_nonunique_sizes(files):
    size_counter = collections.Counter(file.meta.filesize for file in files)
    return [file for file in files if size_counter[file.meta.filesize] > 1]


def find_same_files(audio, files):
    nonunique_hashes_dict = create_nonunique_hashes_dict(files)
    hash = audio.hash
    if hash not in nonunique_hashes_dict:
        return []
    same_hash = nonunique_hashes_dict[hash]
    same_files = compare_and_find_files(audio, same_hash)
    same_files.remove(audio)
    return same_files


def count_hash(files):
    for file in files:
        if file.hash:
            continue
        file.hash = get_hash_md5(file.path())


def get_hash_md5(filename):
    with open(filename, 'rb') as f:
        m = hashlib.md5()
        while True:
            data = f.read(8192)
            if not data:
                break
            m.update(data)
        return m.hexdigest()


def compare_and_find_files(search_file, files):
    same_files = []
    for file in files:
        if files_are_same(search_file, file):
            same_files.append(file)
    return same_files


def files_are_same(file_1, file_2):
    return filecmp.cmp(file_1.path(), file_2.path())


def sort(audio_files, key):
    if len(audio_files) == 0 or not hasattr(audio_files[0], key):
        return audio_files
    return sorted(audio_files, key=operator.attrgetter(key))


def sort_dict_by_key(input_dict):
    return dict(sorted(input_dict.items(), key=operator.itemgetter(0)))

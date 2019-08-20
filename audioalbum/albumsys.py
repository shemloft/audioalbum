from . import files
import os

NAME_EXIST_ERROR = 1


class Album:
    def __init__(self, album_name, album_items):
        self.album_items = album_items
        self.album_name = album_name

    def add_audio_files(self, audio_files):
        for file in audio_files:
            self.add_file(file)

    def add_file(self, file):
        if not hasattr(file, 'name'):
            return
        item = AlbumItem(file)
        self.album_items.append(item)

    def delete_item(self, index):
        if len(self.album_items) <= index or index < 0:
            return
        self.album_items.pop(index)

    def change_item_name(self, index, new_name):
        if len(self.album_items) <= index or index < 0:
            return
        self.album_items[index].name = new_name

    def change_album_name(self, new_name):
        self.album_name = new_name

    def move_item(self, pos, direction):
        item_count = len(self.album_items)
        if item_count == 0 or pos < 0 or pos >= item_count \
                or direction != 'up' and direction != 'down':
            return -1
        new_pos = (pos - 1 + item_count) % item_count \
            if direction == 'up' else (pos + 1) % item_count
        item = self.album_items.pop(pos)
        self.album_items.insert(new_pos, item)
        return new_pos

    def save_album(self):
        items_info = [self.album_name]
        for file in self.album_items:
            items_info.append(file.save_item())
        album_info = '\n\r'.join(items_info) + '\n\r\n\r'
        return album_info


class AlbumItem:
    def __init__(self, audio_file):
        self.audio_file = audio_file
        self.name = self.audio_file.name

    def save_item(self):
        return '{}::{}'.format(self.audio_file.path(), self.name)


class AlbumEditor:
    def __init__(self):
        self.albums = {}

    def add_album(self, album):
        self.albums[album.album_name] = album

    def change_album_name(self, old_name, new_name):
        if new_name in self.albums:
            return NAME_EXIST_ERROR
        album = self.albums.pop(old_name)
        album.change_album_name(new_name)
        self.albums[new_name] = album

    def change_song_name(self, album_name, song_index, new_song_name):
        self.albums[album_name].change_item_name(song_index, new_song_name)

    def save_albums(self):
        saved_albums = ''
        for name, album in self.albums.items():
            saved_albums += album.save_album()
        return saved_albums

    def load_albums(self, albums_str):
        albums_str_list = albums_str.split('\n\n\n\n')
        for album_str in albums_str_list:
            album_items = []
            info = album_str.split('\n\n')
            album_name = info[0]
            if not album_name:
                continue
            info.pop(0)
            for song in info:
                song_info = song.split('::')
                path = song_info[0]
                name = song_info[1]
                if not os.path.exists(path):
                    continue
                file_name = os.path.split(path)
                audio = files.AudioFile(*file_name)
                album_item = AlbumItem(audio)
                album_item.name = name
                album_items.append(album_item)
            album = Album(album_name, album_items)
            self.add_album(album)


class AutoAlbumsMaker:
    def __init__(self, audio_files):
        self.audio_files = audio_files
        self.clear_audio_files()
        self.artist_albums_dict = {}
        self.album_albums_dict = {}
        self.genre_albums_dict = {}
        self.year_albums_dict = {}

    def clear_audio_files(self):
        clear_files = []
        for file in self.audio_files:
            if file.meta is not None:
                clear_files.append(file)
        self.audio_files = clear_files

    def make_albums(self, info):
        key = '{}_albums_dict'.format(info)
        if key not in dir(self):
            return
        info_dict = getattr(self, key)
        clear_files = self.get_files_with_attr(info)
        for file in clear_files:
            file_info = getattr(file.meta, info)
            if file_info not in info_dict:
                info_dict[file_info] = []
            info_dict[file_info].append(file)
        info_dict = files.sort_dict_by_key(info_dict)
        info_dict = {key: Album(key, [AlbumItem(file) for file in value])
                     for key, value in info_dict.items()}
        setattr(self, key, info_dict)

    def get_files_with_attr(self, info):
        clear_files = []
        for file in self.audio_files:
            file_info = getattr(file.meta, info)
            if not file_info:
                continue
            clear_files.append(file)
        return clear_files

    def get_required_albums(self, *albums, all_albums=False):
        required_albums = {}
        if all_albums:
            albums = ['artist', 'album', 'genre', 'year']
        for album in albums:
            key = '{}_albums_dict'.format(album)
            if key not in dir(self):
                continue
            album_dict = getattr(self, key)
            required_albums = {**required_albums, **album_dict}
        return required_albums

    @property
    def artist_albums(self):
        return self.artist_albums_dict

    @property
    def album_albums(self):
        return self.album_albums_dict

    @property
    def genre_albums(self):
        return self.genre_albums_dict

    @property
    def year_albums(self):
        return self.year_albums_dict

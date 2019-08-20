import unittest
import sys
import os
import random
from unittest.mock import patch

sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                             os.path.pardir))
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                             os.path.pardir, 'audioalbum'))
from audioalbum import files, albumsys


class AlbumSaveTests(unittest.TestCase):
    @patch('files.AudioFile')
    def _get_mock_file(self, mock_file):
        file = mock_file()
        return file

    def _get_file(self, name, directory):
        file = self._get_mock_file()
        file.name = name
        file.path.return_value = directory
        return file

    def _get_test_album(self, start, count):
        album = albumsys.Album('name{}'.format(start), [])
        for start in range(start, start + count):
            album.add_file(self._get_file('name{}'.format(start),
                                          'directory{}'.format(start)))
        return album

    def test_save_item(self):
        item = albumsys.AlbumItem(self._get_file('name', 'directory'))
        saved_item = item.save_item()

        self.assertEqual(saved_item, 'directory::name')

    def test_save_album(self):
        album = self._get_test_album(0, 2)
        saved_album = album.save_album()

        self.assertEqual(saved_album,
                         'name0\n\r'
                         'directory0::name0\n\r'
                         'directory1::name1\n\r\n\r')
        pass

    def test_save_few_albums(self):
        album1 = self._get_test_album(0, 3)
        album2 = self._get_test_album(3, 3)
        album_editor = albumsys.AlbumEditor()
        album_editor.add_album(album1)
        album_editor.add_album(album2)

        saved_albums = album_editor.save_albums()

        self.assertEqual(
            saved_albums,
            'name0\n\rdirectory0::name0\n\r'
            'directory1::name1\n\rdirectory2::name2\n\r\n\r'
            'name3\n\rdirectory3::name3\n\r'
            'directory4::name4\n\rdirectory5::name5\n\r\n\r')


class SortTests(unittest.TestCase):
    @patch('files.AudioFile')
    def _get_mock_audio_file(self, mock_file):
        file = mock_file()
        return file

    def _get_list_to_sort(self):
        audio_files = []
        for i in range(0, 10):
            file = self._get_mock_audio_file()
            file.directory = 'directory{}'.format(i)
            file.file_name = 'file_name{}'.format(i)
            file.name = 'name{}'.format(i)
            file.meta.artist = 'artist{}'.format(i)
            file.meta.album = 'album{}'.format(i)
            file.meta.genre = 'genre{}'.format(i)
            file.meta.year = '200{}'.format(i)
            del file.artist
            audio_files.append(file)
        random.shuffle(audio_files)
        return audio_files

    def test_sort_correct_key(self):
        audio_files = self._get_list_to_sort()

        sorted_files = files.sort(audio_files, 'name')

        self.assertEqual(['name{}'.format(i) for i in range(0, 10)],
                         [file.name for file in sorted_files])

    def test_sort_correct_key_two_attributes(self):
        audio_files = self._get_list_to_sort()

        sorted_files = files.sort(audio_files, 'meta.artist')

        self.assertEqual(['artist{}'.format(i) for i in range(0, 10)],
                         [file.meta.artist for file in sorted_files])

    def test_sort_incorrect_key(self):
        audio_files = self._get_list_to_sort()

        sorted_files = files.sort(audio_files, 'artist')

        self.assertEqual(audio_files, sorted_files)

    def test_sort_empty_list(self):
        audio_files = []

        sorted_files = files.sort(audio_files, 'name')

        self.assertEqual(audio_files, sorted_files)


class AutoCreationTest(unittest.TestCase):
    @patch('files.AudioFile')
    def _get_mock_audio_file(self, mock_file):
        file = mock_file()
        return file

    def _get_audio_files_series(self, artist=None, album=None,
                                genre=None, year=None):
        audio_files = []
        for i in range(0, 5):
            file = self._get_mock_audio_file()
            file.meta.title = 'title{}'.format(i)
            file.meta.artist = artist if artist else 'artist{}'.format(i)
            file.meta.album = album if album else 'album{}'.format(i)
            file.meta.genre = genre if genre else 'genre{}'.format(i)
            file.meta.year = year if year else 'year{}'.format(i)
            audio_files.append(file)
        return audio_files

    def _get_meta_none_audio_files_series(self):
        audio_files = []
        for i in range(0, 5):
            file = self._get_mock_audio_file()
            file.meta = None
            audio_files.append(file)
        return audio_files

    def _get_meta_attr_none_audio_files_series(self):
        audio_files = []
        for i in range(0, 5):
            file = self._get_mock_audio_file()
            file.meta.title = 'title{}'.format(i)
            file.meta.artist = None
            file.meta.album = None
            file.meta.genre = None
            file.meta.year = None
            audio_files.append(file)
        return audio_files

    def test_get_rid_of_none(self):
        files1 = self._get_meta_none_audio_files_series()
        files2 = self._get_audio_files_series(artist='test_artist2')

        album_maker = albumsys.AutoAlbumsMaker(files1 + files2)

        self.assertEqual(files2, album_maker.audio_files)

    def test_meta_none(self):
        files1 = self._get_meta_none_audio_files_series()
        files2 = self._get_audio_files_series(artist='test_artist2')

        album_maker = albumsys.AutoAlbumsMaker(files1 + files2)
        album_maker.make_albums('artist')

        albums = album_maker.artist_albums
        self.assertIn('test_artist2', albums)
        self.assertEqual(['test_artist2'], list(albums.keys()))
        self.assertEqual(
            [file.name for file in files2],
            [file.name for file in albums['test_artist2'].album_items])

    def test_meta_attr_none(self):
        files1 = self._get_meta_attr_none_audio_files_series()
        files2 = self._get_audio_files_series(artist='test_artist2')

        album_maker = albumsys.AutoAlbumsMaker(files1 + files2)
        album_maker.make_albums('artist')

        albums = album_maker.artist_albums
        self.assertIn('test_artist2', albums)
        self.assertEqual(['test_artist2'], list(albums.keys()))
        self.assertEqual(
            [file.name for file in files2],
            [file.name for file in albums['test_artist2'].album_items])

    def test_same_artist(self):
        files1 = self._get_audio_files_series(artist='test_artist1')
        files2 = self._get_audio_files_series(artist='test_artist2')
        album_maker = albumsys.AutoAlbumsMaker(files1 + files2)

        album_maker.make_albums('artist')

        albums = album_maker.artist_albums
        self.assertIn('test_artist1', albums)
        self.assertIn('test_artist2', albums)
        self.assertEqual(['test_artist1', 'test_artist2'], list(albums.keys()))
        self.assertEqual(
            [file.name for file in files1],
            [file.name for file in albums['test_artist1'].album_items])
        self.assertEqual(
            [file.name for file in files2],
            [file.name for file in albums['test_artist2'].album_items])

    def test_same_album(self):
        files1 = self._get_audio_files_series(album='test_album1')
        files2 = self._get_audio_files_series(album='test_album2')
        album_maker = albumsys.AutoAlbumsMaker(files1 + files2)

        album_maker.make_albums('album')

        albums = album_maker.album_albums
        self.assertIn('test_album1', albums)
        self.assertIn('test_album2', albums)
        self.assertEqual(['test_album1', 'test_album2'], list(albums.keys()))
        self.assertEqual(
            [file.name for file in files1],
            [file.name for file in albums['test_album1'].album_items])
        self.assertEqual(
            [file.name for file in files2],
            [file.name for file in albums['test_album2'].album_items])

    def test_same_year(self):
        files1 = self._get_audio_files_series(year='2001')
        files2 = self._get_audio_files_series(year='2002')
        all_files = files1 + files2
        random.shuffle(all_files)
        album_maker = albumsys.AutoAlbumsMaker(all_files)

        album_maker.make_albums('year')

        albums = album_maker.year_albums
        self.assertIn('2001', albums)
        self.assertIn('2002', albums)
        self.assertEqual(['2001', '2002'], list(albums.keys()))
        self.assertEqual(len(files1), len(albums['2001'].album_items))
        self.assertEqual(len(files2), len(albums['2002'].album_items))

    def test_same_genre(self):
        files1 = self._get_audio_files_series(genre='genre1')
        files2 = self._get_audio_files_series(genre='genre2')
        album_maker = albumsys.AutoAlbumsMaker(files2 + files1)

        album_maker.make_albums('genre')

        albums = album_maker.genre_albums
        self.assertIn('genre1', albums)
        self.assertIn('genre2', albums)
        self.assertEqual(['genre1', 'genre2'], list(albums.keys()))
        self.assertEqual([file.name for file in files1],
                         [file.name for file in albums['genre1'].album_items])
        self.assertEqual([file.name for file in files2],
                         [file.name for file in albums['genre2'].album_items])

    def test_incorrect_attribute(self):
        files1 = self._get_audio_files_series(artist='test_artist1')
        files2 = self._get_audio_files_series(artist='test_artist2')
        album_maker = albumsys.AutoAlbumsMaker(files1 + files2)

        album_maker.make_albums('title')

        albums = album_maker.get_required_albums(all_albums=True)
        self.assertEqual(0, len(albums))

    def test_incorrect_get_albums(self):
        files1 = self._get_audio_files_series(artist='test_artist1')
        files2 = self._get_audio_files_series(artist='test_artist2')
        album_maker = albumsys.AutoAlbumsMaker(files1 + files2)

        album_maker.make_albums('artist')

        albums = album_maker.get_required_albums('title')

        self.assertEqual(0, len(albums))

    def test_half_correct_get_albums(self):
        files1 = self._get_audio_files_series(artist='test_artist1')
        files2 = self._get_audio_files_series(artist='test_artist2')
        album_maker = albumsys.AutoAlbumsMaker(files1 + files2)

        album_maker.make_albums('artist')

        albums = album_maker.get_required_albums('artist', 'title')

        self.assertIn('test_artist1', albums)
        self.assertIn('test_artist2', albums)
        self.assertEqual(['test_artist1', 'test_artist2'], list(albums.keys()))
        self.assertEqual(
            [file.name for file in files1],
            [file.name for file in albums['test_artist1'].album_items])
        self.assertEqual(
            [file.name for file in files2],
            [file.name for file in albums['test_artist2'].album_items])

    def test_other_half_correct_get_albums(self):
        files1 = self._get_audio_files_series(artist='test_artist1')
        files2 = self._get_audio_files_series(artist='test_artist2')
        album_maker = albumsys.AutoAlbumsMaker(files1 + files2)

        album_maker.make_albums('artist')

        albums = album_maker.get_required_albums('title', 'artist')

        self.assertIn('test_artist1', albums)
        self.assertIn('test_artist2', albums)
        self.assertEqual(['test_artist1', 'test_artist2'], list(albums.keys()))
        self.assertEqual(
            [file.name for file in files1],
            [file.name for file in albums['test_artist1'].album_items])
        self.assertEqual(
            [file.name for file in files2],
            [file.name for file in albums['test_artist2'].album_items])

    def test_few_attributes_in_one(self):
        files1 = self._get_audio_files_series(
            artist='test_artist1', album='test_album1')
        files2 = self._get_audio_files_series(
            artist='test_artist2', album='test_album2')
        album_maker = albumsys.AutoAlbumsMaker(files1 + files2)

        album_maker.make_albums('artist')
        album_maker.make_albums('album')

        albums = album_maker.get_required_albums(all_albums=True)

        self.assertEqual(4, len(albums))
        self.assertIn('test_artist1', albums)
        self.assertIn('test_artist2', albums)
        self.assertIn('test_album1', albums)
        self.assertIn('test_album2', albums)
        self.assertEqual(
            ['test_artist1', 'test_artist2', 'test_album1', 'test_album2'],
            list(albums.keys()))
        self.assertEqual(
            [file.name for file in files1],
            [file.name for file in albums['test_artist1'].album_items])
        self.assertEqual(
            [file.name for file in files2],
            [file.name for file in albums['test_artist2'].album_items])
        self.assertEqual(
            [file.name for file in files1],
            [file.name for file in albums['test_album1'].album_items])
        self.assertEqual(
            [file.name for file in files2],
            [file.name for file in albums['test_album2'].album_items])


class InFilesSearchTest(unittest.TestCase):
    @patch('files.AudioFile')
    def _get_mock_audio_file(self, mock_file):
        file = mock_file()
        return file

    def _get_test_album(self):
        audio_list = self._get_audio_file_list()
        album = albumsys.Album('name', [])
        album.add_audio_files(audio_list)
        return album

    def _get_audio_file_list(self):
        audio_list = []
        for i in range(0, 10):
            if i % 2 == 0:
                file = self._get_mock_audio_file()
                file.name = 'name{}'.format(i)
                audio_list.append(file)
            else:
                file = self._get_mock_audio_file()
                file.name = 'other_name{}'.format(i)
                audio_list.append(file)
        return audio_list

    def _get_another_audio_file_list(self):
        audio_list = []
        for i in range(0, 10):
            file = self._get_mock_audio_file()
            file.name = 'name{}'.format(i)
            audio_list.append(file)
        return audio_list

    def test_find_name_in_files(self):
        audio_list = self._get_audio_file_list()

        result_list = files.find_name_in_files('other', audio_list)

        self.assertEqual(5, len(result_list))
        self.assertIn('other_name3', [file.name for file in result_list])
        self.assertNotIn('name2', [file.name for file in result_list])

    def test_find_name_in_files_no_result(self):
        audio_list = self._get_another_audio_file_list()

        result_list = files.find_name_in_files('other', audio_list)

        self.assertEqual(0, len(result_list))

    def test_find_name_in_albums(self):
        album_editor = albumsys.AlbumEditor()
        album1 = self._get_test_album()
        album1.change_album_name('name1')
        album_editor.add_album(album1)
        album2 = self._get_test_album()
        album2.change_album_name('name2')
        album_editor.add_album(album2)

        result_dict = files.find_name_in_albums('other', album_editor.albums)

        self.assertEqual(2, len(result_dict))
        self.assertIn('name1', result_dict)
        self.assertIn('name2', result_dict)
        self.assertEqual(5, len(result_dict['name1']))
        self.assertEqual(5, len(result_dict['name2']))


class AlbumsTests(unittest.TestCase):
    @patch('files.AudioFile')
    def _get_mock_file(self, mock_file):
        file = mock_file()
        return file

    def _get_test_album(self):
        audio_list = self._get_test_list()
        album = albumsys.Album('name', [])
        album.add_audio_files(audio_list)
        return album

    def _get_test_list(self):
        audio_list = []
        for i in range(0, 10):
            file = self._get_mock_file()
            file.name = 'name{}'.format(i)
            audio_list.append(file)
        return audio_list

    def test_create_album(self):
        album = albumsys.Album('name', ['song1', 'song2', 'song3'])

        self.assertEqual(album.album_name, 'name')
        self.assertEqual(['song1', 'song2', 'song3'], album.album_items)

    def test_add_one_file(self):
        audio_file = self._get_mock_file()
        audio_file.name = 'name'
        album = self._get_test_album()

        album.add_file(audio_file)

        item = album.album_items[10]
        self.assertIsInstance(item, albumsys.AlbumItem)
        self.assertEqual(item.name, 'name')
        self.assertEqual(item.audio_file, audio_file)

    def test_add_one_file_no_attribute(self):
        audio_file = 'file'
        album = self._get_test_album()

        album.add_file(audio_file)

        self.assertEqual(10, len(album.album_items))
        self.assertNotIn(audio_file, album.album_items)

    def test_add_files(self):
        album = self._get_test_album()

        self.assertEqual(10, len(album.album_items))
        self.assertIn('name5', [item.name for item in album.album_items])
        self.assertIn('name0', [item.name for item in album.album_items])
        self.assertIn('name9', [item.name for item in album.album_items])

    def test_delete_item(self):
        album = self._get_test_album()

        album.delete_item(3)

        self.assertEqual(9, len(album.album_items))
        self.assertNotIn('name3', [item.name for item in album.album_items])

    def test_delete_item_incorrect_index(self):
        album = self._get_test_album()

        album.delete_item(10)

        self.assertEqual(10, len(album.album_items))

    def test_change_item_name(self):
        album = self._get_test_album()

        album.change_item_name(3, 'name10')

        self.assertEqual(10, len(album.album_items))
        self.assertNotIn('name3', [item.name for item in album.album_items])
        self.assertIn('name10', [item.name for item in album.album_items])

    def test_change_item_name_incorrect_index(self):
        album = self._get_test_album()

        album.change_item_name(10, 'name10')

        self.assertEqual(10, len(album.album_items))
        self.assertNotIn('name10', [item.name for item in album.album_items])

    def test_change_album_name(self):
        album = self._get_test_album()

        album.change_album_name('new_name')

        self.assertEqual(album.album_name, 'new_name')

    def test_move_item_simple(self):
        album = self._get_test_album()

        album.move_item(2, 'up')

        self.assertEqual(10, len(album.album_items))
        self.assertEqual(album.album_items[1].name, 'name2')
        self.assertEqual(album.album_items[2].name, 'name1')

    def test_move_item_up_border(self):
        album = self._get_test_album()

        album.move_item(0, 'up')

        self.assertEqual(10, len(album.album_items))
        self.assertEqual(album.album_items[0].name, 'name1')
        self.assertEqual(album.album_items[9].name, 'name0')

    def test_move_item_down_border(self):
        album = self._get_test_album()

        album.move_item(9, 'down')

        self.assertEqual(10, len(album.album_items))
        self.assertEqual(album.album_items[0].name, 'name9')
        self.assertEqual(album.album_items[9].name, 'name8')

    def test_move_item_incorrect_start(self):
        album = self._get_test_album()

        album.move_item(10, 'up')

        self.assertEqual(10, len(album.album_items))
        self.assertEqual([file.name for file in self._get_test_list()],
                         [item.name for item in album.album_items])

    def test_move_item_incorrect_direction(self):
        album = self._get_test_album()

        album.move_item(10, 'dup')

        self.assertEqual(10, len(album.album_items))
        self.assertEqual([file.name for file in self._get_test_list()],
                         [item.name for item in album.album_items])

    def test_move_item_empty_list(self):
        album = albumsys.Album('', [])

        album.move_item(10, 'up')

        self.assertEqual(0, len(album.album_items))
        self.assertEqual([], album.album_items)

    def test_add_album(self):
        album_editor = albumsys.AlbumEditor()
        album = self._get_test_album()
        album_editor.add_album(album)

        self.assertEqual(1, len(album_editor.albums))
        self.assertIn('name', album_editor.albums)
        self.assertEqual(album, album_editor.albums['name'])

    def test_add_albums(self):
        album_editor = albumsys.AlbumEditor()
        album1 = self._get_test_album()
        album1.change_album_name('name1')
        album_editor.add_album(album1)
        album2 = self._get_test_album()
        album2.change_album_name('name2')
        album_editor.add_album(album2)

        self.assertEqual(2, len(album_editor.albums))
        self.assertIn('name1', album_editor.albums)
        self.assertIn('name2', album_editor.albums)
        self.assertEqual(album1, album_editor.albums['name1'])
        self.assertEqual(album2, album_editor.albums['name2'])

    def test_change_album_name_editor(self):
        album_editor = albumsys.AlbumEditor()
        album1 = self._get_test_album()
        album1.change_album_name('name1')
        album_editor.add_album(album1)
        album2 = self._get_test_album()
        album2.change_album_name('name2')
        album_editor.add_album(album2)
        album_editor.change_album_name('name2', 'name3')

        self.assertEqual(2, len(album_editor.albums))
        self.assertIn('name1', album_editor.albums)
        self.assertNotIn('name2', album_editor.albums)
        self.assertIn('name3', album_editor.albums)
        self.assertEqual(album1, album_editor.albums['name1'])
        self.assertEqual(album2, album_editor.albums['name3'])

    def test_change_album_name_editor_name_exist(self):
        album_editor = albumsys.AlbumEditor()
        album1 = self._get_test_album()
        album1.change_album_name('name1')
        album_editor.add_album(album1)
        album2 = self._get_test_album()
        album2.change_album_name('name2')
        album_editor.add_album(album2)
        album_editor.change_album_name('name2', 'name1')

        self.assertEqual(2, len(album_editor.albums))
        self.assertIn('name1', album_editor.albums)
        self.assertIn('name2', album_editor.albums)
        self.assertEqual(album1, album_editor.albums['name1'])
        self.assertEqual(album2, album_editor.albums['name2'])

    def test_change_song_name(self):
        album_editor = albumsys.AlbumEditor()
        album = self._get_test_album()
        album_editor.add_album(album)
        album_editor.change_song_name('name', 2, 'name10')

        self.assertEqual(1, len(album_editor.albums))
        self.assertIn('name', album_editor.albums)
        self.assertIn(
            'name10',
            [item.name for item in album_editor.albums['name'].album_items])
        self.assertNotIn(
            'name2',
            [item.name for item in album_editor.albums['name'].album_items])


class FilesSearchTest(unittest.TestCase):
    def test_re(self):
        formats = ['mp3', 'flac', 'wav']
        re = files.create_regexp(formats)
        test_files = \
            ['music.mp3', 'text.txt', 'audio.wav', 'image.jpg', 'sound.ogg']
        audio = []
        for file_name in test_files:
            match = re.match(file_name)
            if not match:
                continue
            audio.append(match.group('file_name'))
        self.assertEqual(len(audio), 2)
        self.assertIn('music.mp3', audio)
        self.assertIn('audio.wav', audio)


if __name__ == '__main__':
    unittest.main()

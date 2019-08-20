#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
import sys
import contextlib
import random
from pathlib import Path
from PyQt5 import QtWidgets, QtCore, QtGui
from audioalbum import files, playback, fsystem, albumsys, clustering


class PlayerWindow(QtWidgets.QMainWindow):
    AUDIO_FILES = list()
    AUDIO_FEATURES = {}
    SAVING_FILE = 'saved_albums.txt'

    def __init__(self, audio_files):
        super().__init__()
        self.AUDIO_FILES = audio_files
        self.playing_files = list(self.AUDIO_FILES)
        self.current_playlist = list(self.AUDIO_FILES)
        self.player = playback.MusicPlayer(self.playing_files)
        self.fs_editor = fsystem.FileSystemEdit(self.playing_files)
        self.album_editor = albumsys.AlbumEditor()
        self.play_row = True
        self.is_pause = False
        self.repeat_track = False
        self.timer_change = False
        self.shuffle = False
        self.file_sys_work = False
        self.icons = {
            'play': QtGui.QIcon('images/play.png'),
            'pause': QtGui.QIcon('images/pause.png'),
            'again': QtGui.QIcon('images/again.png'),
            'cur_song': QtGui.QIcon('images/cur_song.png'),
            'repeat': QtGui.QIcon('images/repeat.png'),
            'no_repeat': QtGui.QIcon('images/no_repeat.png'),
            'shuffle': QtGui.QIcon('images/shuffle.png'),
            'normal': QtGui.QIcon('images/normal.png'),
            'previous': QtGui.QIcon('images/previous.png'),
            'next': QtGui.QIcon('images/next.png'),
            'rewind_f': QtGui.QIcon('images/rewind_f.png'),
            'rewind_b': QtGui.QIcon('images/rewind_b.png')
        }
        self._init_ui()

    def _init_ui(self):

        self.move(100, 200)
        self.setFixedSize(450, 800)
        self.setWindowTitle('Player')

        self.timer = QtCore.QBasicTimer()
        self.step = 0

        menubar = self.menuBar()
        file_menu = menubar.addMenu('File')
        search_menu = menubar.addMenu('Search')
        album_menu = menubar.addMenu('Album')
        cluster_menu = menubar.addMenu('Cluster')

        work_with_album_action = QtWidgets.QAction('Albums', self)
        work_with_album_action.triggered.connect(self.open_album_window)
        album_menu.addAction(work_with_album_action)

        similar_files_action = QtWidgets.QAction('Find similar files', self)
        similar_files_action.triggered.connect(self.open_cluster_window)
        cluster_menu.addAction(similar_files_action)

        clustering_action = QtWidgets.QAction('Cluster all music', self)
        clustering_action.triggered.connect(self.open_all_clusters_window)
        cluster_menu.addAction(clustering_action)

        search_file_action = QtWidgets.QAction('Search files', self)
        search_file_action.setShortcut('Ctrl+F')
        search_file_action.triggered.connect(self.search_files)
        search_menu.addAction(search_file_action)

        search_duplicates_action = QtWidgets.QAction('Search duplicates', self)
        search_duplicates_action.setShortcut('Ctrl+D')
        search_duplicates_action.triggered.connect(self.search_duplicates)
        search_menu.addAction(search_duplicates_action)

        self.delete_file_action = QtWidgets.QAction('Delete', self)
        self.delete_file_action.setShortcut('Del')
        self.delete_file_action.triggered.connect(self.delete_file)
        file_menu.addAction(self.delete_file_action)

        self.rename_file_action = QtWidgets.QAction('Rename', self)
        self.rename_file_action.setShortcut('F2')
        self.rename_file_action.triggered.connect(self.rename_file)
        file_menu.addAction(self.rename_file_action)

        self.move_file_action = QtWidgets.QAction('Move', self)
        self.move_file_action.setShortcut('Ctrl+M')
        self.move_file_action.triggered.connect(self.move_file)
        file_menu.addAction(self.move_file_action)

        self.current_song_title = QtWidgets.QLabel('nothing is playing')
        self.current_song_artist = QtWidgets.QLabel('')

        self.play_pause_button = QtWidgets.QPushButton()
        self.play_pause_button.setIcon(self.icons['play'])
        self.play_pause_button.clicked.connect(self.play_pause)

        self.song_slider = QtWidgets.QSlider(QtCore.Qt.Horizontal)
        self.song_slider.setValue(0)
        self.song_slider.valueChanged.connect(self.rewind)
        self.song_slider.setFixedHeight(10)

        self.again = QtWidgets.QPushButton()
        self.again.setIcon(self.icons['again'])
        self.again.clicked.connect(self.play_again)

        self.repeat = QtWidgets.QPushButton()
        self.repeat.setIcon(self.icons['no_repeat'])
        self.repeat.clicked.connect(self.repeat_this_track)

        self.shuffle_normal = QtWidgets.QPushButton()
        self.shuffle_normal.setIcon(self.icons['normal'])
        self.shuffle_normal.clicked.connect(self.shuffle_back_to_normal)

        self.move_to_cur_track = QtWidgets.QPushButton()
        self.move_to_cur_track.setIcon(self.icons['cur_song'])
        self.move_to_cur_track.clicked.connect(self.move_to_current_track)

        self.next_track = QtWidgets.QPushButton()
        self.next_track.setIcon(self.icons['next'])
        self.next_track.clicked.connect(self.play_next_track)

        self.prev_track = QtWidgets.QPushButton()
        self.prev_track.setIcon(self.icons['previous'])
        self.prev_track.clicked.connect(self.play_previous_track)

        self.volume = QtWidgets.QSlider(QtCore.Qt.Horizontal)
        self.volume.setValue(50)
        self.volume.valueChanged.connect(self.change_volume)
        self.volume.setFixedHeight(10)

        self.volume_label = QtWidgets.QLabel('volume')

        self.audio_list_widget = QtWidgets.QListWidget()
        self.audio_list_widget.itemDoubleClicked.connect(self.play_from_list)
        self.audio_list_widget.itemClicked.connect(self.show_file_info)

        self.file_info_widget = FileInfoWindow()

        volume_box = QtWidgets.QVBoxLayout()

        volume_box.addWidget(self.volume_label)
        self.volume_label.setAlignment(QtCore.Qt.AlignCenter)
        volume_box.addWidget(self.volume)

        buttons_box = QtWidgets.QHBoxLayout()
        buttons_box.addWidget(self.prev_track)
        buttons_box.addWidget(self.play_pause_button)
        buttons_box.addWidget(self.next_track)

        more_buttons_box = QtWidgets.QHBoxLayout()
        more_buttons_box.addWidget(self.again)
        more_buttons_box.addWidget(self.repeat)
        more_buttons_box.addWidget(self.shuffle_normal)
        more_buttons_box.addWidget(self.move_to_cur_track)

        vbox = QtWidgets.QVBoxLayout()
        vbox.addWidget(self.current_song_title)
        vbox.addWidget(self.current_song_artist)
        vbox.addWidget(self.song_slider)
        vbox.addLayout(buttons_box)
        vbox.addLayout(more_buttons_box)
        vbox.addLayout(volume_box)
        vbox.addWidget(self.audio_list_widget)
        vbox.addWidget(self.file_info_widget)

        window = QtWidgets.QWidget(self)
        window.setLayout(vbox)
        self.setCentralWidget(window)

        self.add_files_to_list()

    def play_again(self):
        self.step = 0
        self.player.play_again()

    def rewind(self, value):
        if self.timer_change:
            return
        step = self.player.get_cur_audio_file().meta.duration / 100
        self.player.play_from_position(step * value)
        self.step = round(step*value)

    def repeat_this_track(self):
        if self.repeat_track:
            self.repeat_track = False
            self.repeat.setIcon(self.icons['no_repeat'])
        else:
            self.repeat_track = True
            self.repeat.setIcon(self.icons['repeat'])

    def shuffle_back_to_normal(self):
        current_audio = self.player.get_cur_audio_file()
        self.clear_playing_item()
        if not self.shuffle:
            self.shuffle_normal.setIcon(self.icons['shuffle'])
            random.shuffle(self.playing_files)
            self.add_files_to_list()
            self.shuffle = True
        else:
            self.shuffle_normal.setIcon(self.icons['normal'])
            self.playing_files = list(self.current_playlist)
            self.add_files_to_list()
            self.shuffle = False
        index = self.playing_files.index(current_audio)
        self.player.current_audio = index
        self.move_to_current_track()

    def move_to_current_track(self):
        self.clear_playing_item()
        self.audio_list_widget.setCurrentRow(self.player.current_audio)
        self.highlight_item()

    def play_from_list(self):
        self.play_row = True
        self.play_pause()

    def play_pause(self):
        row = self.audio_list_widget.currentRow()
        self.clear_playing_item()
        if self.play_row:
            self.play_music_from_row(row)
        elif self.is_pause:
            self.player.play(self.player.current_audio)
            self.set_current_audio_text('play')
            self.play_pause_button.setIcon(self.icons['pause'])
            self.is_pause = False
        else:
            self.player.pause()
            self.set_current_audio_text('pause')
            self.play_pause_button.setIcon(self.icons['play'])
            self.is_pause = True
        self.highlight_item()

    def play_music_from_row(self, row):
        if self.is_pause:
            self.player.play(row)
        self.player.play(row)
        self.set_current_audio_text('play')
        self.timer.start(1000, self)
        self.step = 0
        self.play_pause_button.setIcon(self.icons['pause'])
        self.play_row = False
        self.is_pause = False

    def play_next_track(self):
        self.clear_playing_item()
        self.is_pause = False
        self.player.play_next()
        self.step = 0
        self.set_current_audio_text('play')
        self.play_pause_button.setIcon(self.icons['pause'])
        self.highlight_item()

    def play_previous_track(self):
        self.clear_playing_item()
        self.is_pause = False
        self.player.play_previous()
        self.step = 0
        self.set_current_audio_text('play')
        self.play_pause_button.setIcon(self.icons['pause'])
        self.highlight_item()

    def change_volume(self, value):
        self.player.change_volume(value / 100)

    def open_album_window(self):
        self.album_window = AlbumWindow(self)
        self.album_window.show()

    def open_cluster_window(self):
        self.cluster_window = ClusteringWindow(self)
        self.cluster_window.show()

    def open_all_clusters_window(self):
        self.all_cluster_window = AllClustersWindow(self)
        self.all_cluster_window.show()

    def search_files(self):
        self.search = SearchWindow(self.playing_files, self)
        self.search.show()

    def search_duplicates(self):
        self.duplicates = DuplicateWindow(self.playing_files, self)
        self.duplicates.show()

    def show_file_info(self):
        self.file_info_widget.show_file_info(
            self.playing_files[self.audio_list_widget.currentRow()])

    def set_current_audio_text(self, state):
        if state == 'play':
            pic = '► '
            space = '    '
        elif state == 'pause':
            pic = '▌▌ '
            space = '     '
        else:
            return
        text = self.get_text()
        self.current_song_title.setText(pic + text[0])
        self.current_song_artist.setText(space + text[1])

    def get_text(self):
        audio = self.player.get_cur_audio_file()
        title = (
            audio.meta.title if audio.meta and audio.meta.title
            else audio.name)
        artist = (
            audio.meta.artist if audio.meta and audio.meta.artist
            else '<unknown>')
        return title, artist

    def delete_file(self):
        row = self.audio_list_widget.currentRow()
        file = self.playing_files[row]

        reply = QtWidgets.QMessageBox.question(
            self, 'Delete file',
            'Are you sure you want to delete this file?\r\n' + file.name,
            QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No,
            QtWidgets.QMessageBox.No)
        if reply == QtWidgets.QMessageBox.No:
            return

        play_this_row = False
        if self.player.current_audio == row:
            self.player.stop()
            play_this_row = True

        exit_code = self.fs_editor.delete_file(row)
        if not exit_code == fsystem.ERROR_DELETE:
            self.playing_files.remove(file)
            self.AUDIO_FILES.remove(file)
            self.audio_list_widget.takeItem(row)
            self.player.current_audio -= 1

        if play_this_row:
            self.player.restart()
            self.player.play(row)
            self.set_current_audio_text('play')

        self.file_info_widget.clear_info()

    def rename_file(self):
        text, ok = QtWidgets.QInputDialog.getText(
            self, 'Rename file',
            'Enter new file name: ')
        if not ok:
            return

        row = self.audio_list_widget.currentRow()
        play_this_again = False

        self.file_sys_work = True

        if self.player.current_audio == row:
            play_this_again = True
            self.player.stop()

        exit_code = self.fs_editor.rename_file(row, text)
        if not exit_code == fsystem.ERROR_RENAME:
            self.playing_files[row].name = text
            self.playing_files[row].file_name = '{}.{}'.format(
                text, self.playing_files[row].format)
            self.audio_list_widget.takeItem(row)
            self.audio_list_widget.insertItem(row, text)

        self.audio_list_widget.setCurrentRow(row)
        if play_this_again:
            self.player.restart()
            self.step = 0
            self.player.play(row)
            self.set_current_audio_text('play')

        self.file_sys_work = False
        self.file_info_widget.show_file_info(self.playing_files[row])

    def move_file(self):
        new_directory = QtWidgets.QFileDialog.getExistingDirectory(
            self, 'Choose directory')
        row = self.audio_list_widget.currentRow()

        self.file_sys_work = True
        play_this_again = False
        if self.player.current_audio == row:
            play_this_again = True
            self.player.stop()

        exit_code = self.fs_editor.move_file(row, new_directory)
        if not exit_code == fsystem.ERROR_MOVE:
            self.playing_files[row].directory = new_directory

        self.audio_list_widget.setCurrentRow(row)
        if play_this_again:
            self.audio_list_widget.setCurrentRow(row)
            self.player.restart()
            self.step = 0
            self.player.play(row)
            self.set_current_audio_text('play')

        self.file_sys_work = False
        self.file_info_widget.show_file_info(self.playing_files[row])

    def add_files_to_list(self):
        self.audio_list_widget.clear()
        self.player.audio_files = self.playing_files
        self.audio_list_widget.addItems(
            [file.name for file in self.playing_files])
        self.audio_list_widget.setCurrentRow(0)

    def add_album_to_list(self, album):
        self.audio_list_widget.clear()
        self.current_playlist = [item.audio_file for item in album.album_items]
        self.playing_files = [item.audio_file for item in album.album_items]
        self.player.current_audio = 0
        self.player.audio_files = self.playing_files
        self.audio_list_widget.addItems(
            [item.name for item in album.album_items])
        self.audio_list_widget.setCurrentRow(0)
        self.play_row = True
        self.play_pause_button.setIcon(self.icons['play'])

    def highlight_item(self):
        self.audio_list_widget.item(self.player.current_audio).setBackground(
            QtGui.QBrush(QtGui.QColor(161, 248, 96)))

    def clear_playing_item(self):
        self.audio_list_widget.item(self.player.current_audio).setBackground(
            QtGui.QBrush(QtGui.QColor(255, 255, 255)))

    def timerEvent(self, e):
        if self.is_pause or self.file_sys_work:
            return
        if not self.player.music_is_playing():
            if self.repeat_track:
                self.player.play(self.player.current_audio)
                self.step = 0
            else:
                self.play_next_track()
        cur_song_position = \
            self.step / self.player.get_cur_audio_file().meta.duration * 100
        self.timer_change = True
        self.song_slider.setValue(round(cur_song_position))
        self.timer_change = False
        self.step += 1

    def closeEvent(self, event):
        with contextlib.suppress(Exception):
            self.search.close()
        with contextlib.suppress(Exception):
            self.duplicates.close()
        with contextlib.suppress(Exception):
            self.album_window.close()
        with contextlib.suppress(Exception):
            self.cluster_window.close()
        with contextlib.suppress(Exception):
            self.all_cluster_window.close()


class AlbumWindow(QtWidgets.QTabWidget):
    def __init__(self, window):
        super().__init__()
        self.window = window
        self.album_editor = self.window.album_editor

        self._init_ui()

    def _init_ui(self):
        self.setFixedSize(500, 620)

        self.edit_tab = AlbumEditWidget(self.window, self)
        self.search_tab = AlbumSearchWidget(self.album_editor)
        self.auto_tab = AlbumAutoCreationWidget(
            self.window.AUDIO_FILES, self.album_editor)
        self.home_tab = AlbumWindowHomeWidget(self.album_editor, self)

        self.addTab(self.home_tab, 'Albums')
        self.addTab(self.edit_tab, 'Edit')
        self.setTabEnabled(1, False)
        self.addTab(self.search_tab, 'Search')

        self.addTab(self.auto_tab, 'Auto')

        self.currentChanged.connect(self.process_tab_change)

    def process_tab_change(self):
        index = self.currentIndex()
        if index == 0:
            self.home_tab.update_albums()
        if index != 1:
            self.edit_tab.album_list_widget.clear()
            self.edit_tab.name_edit.clear()
            self.setTabEnabled(1, False)
            self.edit_tab.is_edit = False
            self.edit_tab.is_new_album = False
            self.edit_tab.album = None

        if index != 2:
            self.search_tab.search_edit.clear()
            self.search_tab.albums_list_widget.clear()
            self.search_tab.search_result_widget.clear()


class AlbumWindowHomeWidget(QtWidgets.QWidget):
    def __init__(self, album_editor, window):
        super().__init__()
        self.album_editor = album_editor
        self.window = window
        self._init_ui()

    def _init_ui(self):
        self.setFixedSize(500, 600)

        self.album_names_widget = QtWidgets.QListWidget()
        self.update_albums()
        self.edit_button = QtWidgets.QPushButton('Edit')
        self.edit_button.clicked.connect(self.edit_album)
        self.new_album_button = QtWidgets.QPushButton('New album')
        self.new_album_button.clicked.connect(self.create_new_album)
        self.load_button = QtWidgets.QPushButton('Load albums')
        self.load_button.clicked.connect(self.load_albums)
        self.save_all_button = QtWidgets.QPushButton('Save all albums')
        self.save_all_button.clicked.connect(self.save_albums)

        vbox = QtWidgets.QVBoxLayout()
        vbox.addWidget(self.edit_button)
        vbox.addWidget(self.new_album_button)
        vbox.addWidget(self.load_button)
        vbox.addWidget(self.save_all_button)

        hbox = QtWidgets.QHBoxLayout()
        hbox.addWidget(self.album_names_widget)
        hbox.addLayout(vbox)

        self.setLayout(hbox)

    def edit_album(self):
        if len(self.album_editor.albums) == 0:
            return
        self.window.setTabEnabled(1, True)
        self.window.edit_tab.edit_album(
            self.album_editor.albums[
                self.album_names_widget.currentItem().text()]
        )
        self.window.setCurrentIndex(1)

    def create_new_album(self):
        self.window.setTabEnabled(1, True)
        self.window.edit_tab.new_album()
        self.window.setCurrentIndex(1)

    def load_albums(self):
        with open(self.window.window.SAVING_FILE, 'at') as f:
            pass
        with open(self.window.window.SAVING_FILE, 'rt') as f:
            albums = f.read()
        self.album_editor.load_albums(albums)
        self.update_albums()

    def save_albums(self):
        with open(self.window.window.SAVING_FILE, 'at') as f:
            f.write(self.album_editor.save_albums())

    def update_albums(self):
        self.album_names_widget.clear()
        self.album_names_widget.addItems(
            [album for album in self.album_editor.albums])


class AlbumSearchWidget(QtWidgets.QWidget):
    def __init__(self, album_editor):
        super().__init__()
        self.album_editor = album_editor

        self._init_ui()

    def _init_ui(self):

        self.search_edit = QtWidgets.QLineEdit()
        self.search_edit.textChanged.connect(self.search_text)
        self.albums_list_widget = QtWidgets.QListWidget()
        self.albums_list_widget.itemClicked.connect(self.show_result)
        self.search_result_widget = QtWidgets.QListWidget()

        hbox = QtWidgets.QHBoxLayout()
        hbox.addWidget(self.albums_list_widget)
        hbox.addWidget(self.search_result_widget)

        vbox = QtWidgets.QVBoxLayout()
        vbox.addWidget(self.search_edit)
        vbox.addLayout(hbox)

        self.setLayout(vbox)

    def search_text(self, text):
        self.albums_list_widget.clear()
        self.search_result_widget.clear()
        if text == '':
            return
        self.result_dict = files.find_name_in_albums(
            text, self.album_editor.albums)
        if not self.result_dict:
            return
        self.albums_list_widget.addItems(self.result_dict.keys())

    def show_result(self):
        album_name = self.albums_list_widget.currentItem().text()
        self.search_result_widget.clear()
        self.search_result_widget.addItems(
            [item.name for item in self.result_dict[album_name]])


class AlbumAutoCreationWidget(QtWidgets.QWidget):
    def __init__(self, audio_files, album_editor):
        super().__init__()
        self.album_editor = album_editor
        self.audio_files = audio_files
        self.album_maker = albumsys.AutoAlbumsMaker(self.audio_files)
        self.album_maker.make_albums('artist')
        self.album_maker.make_albums('album')
        self.album_maker.make_albums('genre')
        self.album_maker.make_albums('year')
        self.albums = {}
        self._init_ui()

    def _init_ui(self):
        self.artist_box = QtWidgets.QCheckBox('Artist')
        self.artist_box.stateChanged.connect(self.state_changed)
        self.album_box = QtWidgets.QCheckBox('Album')
        self.album_box.stateChanged.connect(self.state_changed)
        self.genre_box = QtWidgets.QCheckBox('Genre')
        self.genre_box.stateChanged.connect(self.state_changed)
        self.year_box = QtWidgets.QCheckBox('Year')
        self.year_box.stateChanged.connect(self.state_changed)

        self.albums_widget = QtWidgets.QListWidget()
        self.albums_widget.itemClicked.connect(self.show_content)
        self.albums_content_widget = QtWidgets.QListWidget()

        self.save_button = QtWidgets.QPushButton('Save')
        self.save_button.clicked.connect(self.save_album)
        self.save_all_button = QtWidgets.QPushButton('Save all')
        self.save_all_button.clicked.connect(self.save_all_albums)

        vbox1 = QtWidgets.QVBoxLayout()
        vbox1.addWidget(self.artist_box)
        vbox1.addWidget(self.album_box)
        vbox1.addWidget(self.genre_box)
        vbox1.addWidget(self.year_box)

        hbox1 = QtWidgets.QHBoxLayout()
        hbox1.addWidget(self.save_button)
        hbox1.addWidget(self.save_all_button)

        hbox2 = QtWidgets.QHBoxLayout()
        hbox2.addLayout(vbox1)
        hbox2.addWidget(self.albums_widget)
        hbox2.addWidget(self.albums_content_widget)

        vbox2 = QtWidgets.QVBoxLayout()
        vbox2.addLayout(hbox2)
        vbox2.addLayout(hbox1)

        self.setLayout(vbox2)

    def save_album(self):
        album_name = self.albums_widget.currentItem().text()
        album = self.albums[album_name]
        if self.check_name_exist_continue(album_name):
            self.album_editor.add_album(album)

    def save_all_albums(self):
        for album_name in self.albums:
            if self.check_name_exist_continue(album_name):
                self.album_editor.add_album(self.albums[album_name])

    def check_name_exist_continue(self, name):
        if name in self.album_editor.albums:
            reply = QtWidgets.QMessageBox.question(
                self, 'The name exist',
                'Album with this name already exist. '
                'Are sure you want to rewrite it?\r\n' + name,
                QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No,
                QtWidgets.QMessageBox.No)
            if reply == QtWidgets.QMessageBox.No:
                return False
        return True

    def state_changed(self):
        artist = 'artist' if self.artist_box.checkState() else ''
        album = 'album' if self.album_box.checkState() else ''
        genre = 'genre' if self.genre_box.checkState() else ''
        year = 'year' if self.year_box.checkState() else ''
        self.albums = self.album_maker.get_required_albums(
            artist, album, genre, year)
        self.albums_widget.clear()
        self.albums_content_widget.clear()
        self.albums_widget.addItems(self.albums.keys())

    def show_content(self):
        album_name = self.albums_widget.currentItem().text()
        album_content = self.albums[album_name].album_items
        self.albums_content_widget.clear()
        self.albums_content_widget.addItems(
            [file.name for file in album_content])


class AlbumEditWidget(QtWidgets.QWidget):
    def __init__(self, window, tab):
        super().__init__()
        self.window = window
        self.tab = tab
        self.is_edit = False
        self.is_new_album = False
        self.is_play = False
        self.album = albumsys.Album('', [])

        self._init_ui()

    def _init_ui(self):
        self.setFixedSize(500, 600)
        self.setAttribute(QtCore.Qt.WA_DeleteOnClose, True)

        self.window.delete_file_action.setEnabled(False)
        self.window.rename_file_action.setEnabled(False)
        self.window.move_file_action.setEnabled(False)

        self.album_list_widget = QtWidgets.QListWidget()
        self.album_list_widget.itemDoubleClicked.connect(self.change_song_name)

        self.move_down_button = QtWidgets.QPushButton('▼')
        self.move_down_button.clicked.connect(self.move_down)
        self.move_up_button = QtWidgets.QPushButton('▲')
        self.move_up_button.clicked.connect(self.move_up)
        self.add_item_button = QtWidgets.QPushButton('Add')
        self.add_item_button.clicked.connect(self.add_to_album)
        self.delete_button = QtWidgets.QPushButton('Delete')
        self.delete_button.clicked.connect(self.delete_item)

        self.save_in_program_button = QtWidgets.QPushButton('Save (prog)')
        self.save_in_program_button.clicked.connect(self.save_in_program)
        self.save_to_computer_button = QtWidgets.QPushButton('Save (comp)')
        self.save_to_computer_button.clicked.connect(self.save_to_computer)
        self.add_all_button = QtWidgets.QPushButton('Add all')
        self.add_all_button.clicked.connect(self.add_all)
        self.play_album_button = QtWidgets.QPushButton('Play')
        self.play_album_button.clicked.connect(self.play)

        self.name_edit = QtWidgets.QLineEdit()
        self.name_edit.textChanged.connect(self.change_name)

        hbox1 = QtWidgets.QHBoxLayout()
        hbox1.addWidget(self.move_up_button)
        hbox1.addWidget(self.move_down_button)
        hbox1.addWidget(self.add_item_button)
        hbox1.addWidget(self.delete_button)

        hbox2 = QtWidgets.QHBoxLayout()
        hbox2.addWidget(self.add_all_button)
        hbox2.addWidget(self.play_album_button)
        hbox2.addWidget(self.save_in_program_button)
        hbox2.addWidget(self.save_to_computer_button)

        vbox = QtWidgets.QVBoxLayout()
        vbox.addWidget(self.name_edit)
        vbox.addLayout(hbox1)
        vbox.addWidget(self.album_list_widget)
        vbox.addLayout(hbox2)
        self.setLayout(vbox)

    def edit_album(self, album):
        self.is_edit = True
        self.is_new_album = False
        self.save_in_program_button.setEnabled(False)
        self.album = album
        self.name_edit.setText(self.album.album_name)
        self.album_list_widget.clear()
        self.album_list_widget.addItems(
            [item.name for item in self.album.album_items])

    def new_album(self):
        self.is_edit = False
        self.is_new_album = True
        self.save_in_program_button.setEnabled(True)
        self.album = albumsys.Album('', [])
        self.album_list_widget.clear()
        self.name_edit.clear()

    def change_name(self):
        new_name = self.name_edit.text()
        if self.is_new_album:
            self.album.change_album_name(new_name)
        else:
            self.window.album_editor.change_album_name(
                self.album.album_name, new_name)

    def change_song_name(self):
        new_name, ok = QtWidgets.QInputDialog.getText(
            self, 'Rename song',
            'Enter new song name: ')
        if not ok:
            return
        row = self.album_list_widget.currentRow()
        self.album.change_item_name(row, new_name)
        self.album_list_widget.takeItem(row)
        self.album_list_widget.insertItem(row, new_name)

    def save_in_program(self):
        if self.album.album_name in self.window.album_editor.albums:
            reply = QtWidgets.QMessageBox.question(
                self, 'The name exist',
                'Album with this name already exist. '
                'Are sure you want to rewrite it?\r\n' + self.album.album_name,
                QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No,
                QtWidgets.QMessageBox.No)
            if reply == QtWidgets.QMessageBox.No:
                return
        if self.is_new_album:
            self.window.album_editor.add_album(self.album)
            if not self.is_play:
                self.tab.setCurrentIndex(0)
                self.tab.setTabEnabled(1, False)

    def save_to_computer(self):
        with open(self.window.SAVING_FILE, 'at') as f:
            f.write(self.album.save_album())

    def move_item(self, direction):
        row = self.album_list_widget.currentRow()
        new_pos = self.album.move_item(row, direction)
        if new_pos == -1:
            return
        widget_item = self.album_list_widget.takeItem(row)
        self.album_list_widget.insertItem(new_pos, widget_item)
        self.album_list_widget.setCurrentRow(new_pos)

    def move_down(self):
        self.move_item('down')

    def move_up(self):
        self.move_item('up')

    def add_all(self):
        self.album.add_audio_files(self.window.AUDIO_FILES)
        self.album_list_widget.addItems(
            [file.name for file in self.window.AUDIO_FILES])

    def play(self):
        self.is_play = True
        if self.is_new_album:
            self.save_in_program()
        self.window.add_album_to_list(self.album)
        if self.is_new_album:
            self.is_play = False
        self.tab.setCurrentIndex(0)
        self.tab.setTabEnabled(1, False)

    def add_to_album(self):
        file = self.window.playing_files[
            self.window.audio_list_widget.currentRow()]
        self.album.add_file(file)
        self.album_list_widget.addItem(file.name)

    def delete_item(self):
        row = self.album_list_widget.currentRow()
        self.album_list_widget.takeItem(row)
        self.album.delete_item(row)

    def closeEvent(self, event):
        self.window.delete_file_action.setEnabled(True)
        self.window.rename_file_action.setEnabled(True)
        self.window.move_file_action.setEnabled(True)


class DuplicateWindow(QtWidgets.QWidget):
    def __init__(self, files, main_window):
        super().__init__()
        self.window = main_window
        self.files = files
        self.same_files = []

        self._init_ui()

    def _init_ui(self):
        self.setWindowTitle('Search duplicates')
        self.setFixedSize(400, 600)
        self.setAttribute(QtCore.Qt.WA_DeleteOnClose, True)

        self.window.delete_file_action.setEnabled(False)
        self.window.rename_file_action.setEnabled(False)
        self.window.move_file_action.setEnabled(False)

        self.window.audio_list_widget.itemClicked.connect(
            self.search_duplicates)

        self.find_all_button = QtWidgets.QPushButton('find all')
        self.find_all_button.clicked.connect(self.find_all)

        self.current_audio = QtWidgets.QLabel('choose audio')

        self.duplicates_list = QtWidgets.QListWidget()
        self.duplicates_list.itemClicked.connect(self.show_file_info)

        self.file_info_widget = FileInfoWindow()

        vbox = QtWidgets.QVBoxLayout()
        vbox.addWidget(self.current_audio)
        vbox.addWidget(self.duplicates_list)
        vbox.addWidget(self.file_info_widget)
        vbox.addWidget(self.find_all_button)

        self.setLayout(vbox)

    def find_all(self):
        reps = files.find_all_repetitions(self.files)
        self.duplicates_window = AllDuplicationWindow(reps)
        self.duplicates_window.show()

    def search_duplicates(self):
        self.duplicates_list.clear()
        audio = self.files[self.window.audio_list_widget.currentRow()]
        self.current_audio.setText(audio.name)
        self.same_files = files.find_same_files(audio, self.files)

        self.duplicates_list.addItems([file.name for file in self.same_files])

    def show_file_info(self):
        file = self.same_files[self.duplicates_list.currentRow()]
        self.file_info_widget.show_file_info(file)

    def closeEvent(self, event):
        self.window.delete_file_action.setEnabled(True)
        self.window.rename_file_action.setEnabled(True)
        self.window.move_file_action.setEnabled(True)
        with contextlib.suppress(Exception):
            self.duplicates_window.close()


class AllDuplicationWindow(QtWidgets.QWidget):
    def __init__(self, reps):
        super().__init__()
        self.reps = reps
        self._init_ui()

    def _init_ui(self):
        self.resize(500, 500)

        self.first_file_label = QtWidgets.QLabel('Name')
        self.sets_of_repitions = QtWidgets.QListWidget()
        self.sets_of_repitions.addItems([x for x in self.reps])
        self.sets_of_repitions.itemClicked.connect(self.show_reps)

        self.duplication_set_label = QtWidgets.QLabel('File duplicates')
        self.duplication_sets = QtWidgets.QListWidget()
        self.duplication_sets.itemClicked.connect(self.show_file_info)

        self.file_info_widget = FileInfoWindow()

        vbox_1 = QtWidgets.QVBoxLayout()
        vbox_1.addWidget(self.first_file_label)
        vbox_1.addWidget(self.sets_of_repitions)

        vbox_2 = QtWidgets.QVBoxLayout()
        vbox_2.addWidget(self.duplication_set_label)
        vbox_2.addWidget(self.duplication_sets)

        hbox = QtWidgets.QHBoxLayout()
        hbox.addLayout(vbox_1)
        hbox.addLayout(vbox_2)

        vbox = QtWidgets.QVBoxLayout()
        vbox.addLayout(hbox)
        vbox.addWidget(self.file_info_widget)

        self.setLayout(vbox)

    def show_reps(self):
        self.duplication_sets.clear()
        duplication_set = self.reps[
            self.sets_of_repitions.currentItem().text()]
        self.duplication_sets.addItems([file.name for file in duplication_set])

    def show_file_info(self):
        file = self.reps[
            self.sets_of_repitions.currentItem().text()][
            self.duplication_sets.currentRow()]
        self.file_info_widget.show_file_info(file)


class SearchWindow(QtWidgets.QWidget):
    def __init__(self, files, main_window):
        super().__init__()
        self.window = main_window
        self.files = files
        self.founded_files = []

        self.index_files()
        self._init_ui()

    def _init_ui(self):
        self.setWindowTitle('Search')
        self.move(650, 200)
        self.setFixedSize(400, 600)

        self.window.delete_file_action.setEnabled(False)
        self.window.rename_file_action.setEnabled(False)
        self.window.move_file_action.setEnabled(False)

        search_edit = QtWidgets.QLineEdit()
        search_edit.textChanged.connect(self.search_files)

        self.result_list = QtWidgets.QListWidget()
        self.result_list.itemDoubleClicked.connect(self.play)

        vbox = QtWidgets.QVBoxLayout()
        vbox.addWidget(search_edit)
        vbox.addWidget(self.result_list)

        self.setLayout(vbox)

    def search_files(self, text):
        self.result_list.clear()
        if text == '':
            return
        self.founded_files = files.find_name_in_files(text, self.files)
        self.result_list.addItems([file.name for file in self.founded_files])

    def play(self):
        row = self.result_list.currentRow()
        index = self.founded_files[row].index
        self.window.audio_list_widget.setCurrentRow(index)
        self.window.play_row = True
        self.window.play_pause()

        return index

    def index_files(self):
        for (i, file) in enumerate(self.files):
            file.index = i

    def closeEvent(self, event):
        self.window.delete_file_action.setEnabled(True)
        self.window.rename_file_action.setEnabled(True)
        self.window.move_file_action.setEnabled(True)


class FileInfoWindow(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        self._init_ui()

    def _init_ui(self):
        grid = QtWidgets.QGridLayout()
        self.setLayout(grid)

        name_title = QtWidgets.QLabel('Name')
        self.name = QtWidgets.QLabel('')

        artist_title = QtWidgets.QLabel('Artist')
        self.artist = QtWidgets.QLabel('')

        album_title = QtWidgets.QLabel('Album')
        self.album = QtWidgets.QLabel('')

        year_title = QtWidgets.QLabel('Year')
        self.year = QtWidgets.QLabel('')

        duration_title = QtWidgets.QLabel('Duration')
        self.duration = QtWidgets.QLabel('')

        genre_title = QtWidgets.QLabel('Genre')
        self.genre = QtWidgets.QLabel('')

        location_title = QtWidgets.QLabel('Location')
        self.location = QtWidgets.QLabel('')

        filename_title = QtWidgets.QLabel('File name')
        self.filename = QtWidgets.QLabel('')

        size_title = QtWidgets.QLabel('Size')
        self.size = QtWidgets.QLabel('')

        grid.setColumnMinimumWidth(0, 50)
        grid.setColumnMinimumWidth(1, 400)

        grid.addWidget(name_title, 0, 0)
        grid.addWidget(self.name, 0, 1)
        grid.addWidget(artist_title, 1, 0)
        grid.addWidget(self.artist, 1, 1)
        grid.addWidget(album_title, 2, 0)
        grid.addWidget(self.album, 2, 1)
        grid.addWidget(year_title, 3, 0)
        grid.addWidget(self.year, 3, 1)
        grid.addWidget(duration_title, 4, 0)
        grid.addWidget(self.duration, 4, 1)
        grid.addWidget(genre_title, 5, 0)
        grid.addWidget(self.genre, 5, 1)
        grid.addWidget(location_title, 6, 0)
        grid.addWidget(self.location, 6, 1)
        grid.addWidget(filename_title, 7, 0)
        grid.addWidget(self.filename, 7, 1)
        grid.addWidget(size_title, 8, 0)
        grid.addWidget(self.size, 8, 1)

    def show_file_info(self, file):
        self.name.setText(file.meta.title if file.meta else '')
        self.artist.setText(file.meta.artist if file.meta else '')
        self.album.setText(file.meta.album if file.meta else '')
        self.year.setText(file.meta.year[:4]
                          if file.meta and file.meta.year else '')
        self.duration.setText(
            '{}:{:02}'.format(
                round(file.meta.duration // 60),
                round(file.meta.duration % 60))
            if file.meta else '')
        self.genre.setText(file.meta.genre if file.meta else '')
        self.location.setText(file.directory)
        self.filename.setText(file.file_name)
        self.size.setText(
            '{} MB'.format(round(file.meta.filesize / 1024 ** 2, 2))
            if file.meta else '')

    def clear_info(self):
        self.name.setText('')
        self.artist.setText('')
        self.album.setText('')
        self.year.setText('')
        self.duration.setText('')
        self.genre.setText('')
        self.location.setText('')
        self.filename.setText('')
        self.size.setText('')


class ClusteringWindow(QtWidgets.QWidget):
    def __init__(self, window):
        super().__init__()
        self.window = window
        self.audio_list = self.window.current_playlist
        self.audio_features_list = []
        self.number = 2 if len(self.audio_list) < 10 else 10
        self._init_ui()

    def _init_ui(self):
        self.setWindowTitle('Similar files')
        self.move(650, 200)
        self.setFixedSize(600, 600)

        self.find_similar_files_btn = \
            QtWidgets.QPushButton('Find similar files')
        self.find_similar_files_btn.clicked.connect(self.find_clusters)

        self.progressbar = QtWidgets.QProgressBar(self)
        self.progressbar.setMaximum(len(self.audio_list) - 1)

        self.similar_files_widget = QtWidgets.QListWidget()

        vbox = QtWidgets.QVBoxLayout()
        vbox.addWidget(self.find_similar_files_btn)
        vbox.addWidget(self.progressbar)
        vbox.addWidget(self.similar_files_widget)
        self.setLayout(vbox)

    def find_clusters(self):
        self.i = 0

        self.thread = AudioAnalysisThread(self)
        self.thread.start()

        self.thread.finished.connect(self.process_finished)
        self.thread.audio_processed.connect(self.change_progressbar)

    def change_progressbar(self):
        self.progressbar.setValue(self.i)
        self.i += 1

    def process_finished(self):
        features_dict = {features.audio_file: features
                         for features in self.audio_features_list}

        self.clusters = clustering.clusters(
            self.audio_features_list, self.number)

        audio = self.audio_list[self.window.audio_list_widget.currentRow()]
        features = features_dict[audio]

        cluster_index = features.cluster_index

        self.similar_audio = self.clusters[cluster_index]

        self.similar_files_widget.clear()

        self.similar_files_widget.addItems(
            [item.audio_file.name for item in self.similar_audio
             if item.audio_file != audio])


class AllClustersWindow(QtWidgets.QWidget):
    def __init__(self, window):
        super().__init__()
        self.window = window
        self.audio_list = self.window.current_playlist
        self.audio_features_list = []
        self.number = 0
        self._init_ui()

    def _init_ui(self):
        self.setWindowTitle('Clusters')
        self.move(650, 200)
        self.setFixedSize(600, 600)

        self.cluster_number_label = QtWidgets.QLabel(
            'Введите количество кластеров')

        self.progressbar = QtWidgets.QProgressBar(self)
        self.progressbar.setMaximum(len(self.audio_list) - 1)

        self.clusters_number_edit = QtWidgets.QLineEdit(self)
        self.clusters_number_edit.textChanged.connect(self.find_clusters)

        self.cluster_list_widget = QtWidgets.QListWidget()
        self.cluster_list_widget.itemClicked.connect(self.show_result)
        self.cluster_content_widget = QtWidgets.QListWidget()

        hbox1 = QtWidgets.QHBoxLayout()
        hbox1.addWidget(self.cluster_list_widget)
        hbox1.addWidget(self.cluster_content_widget)

        hbox2 = QtWidgets.QHBoxLayout()
        hbox2.addWidget(self.cluster_number_label)
        hbox2.addWidget(self.clusters_number_edit)

        vbox = QtWidgets.QVBoxLayout()
        vbox.addLayout(hbox2)
        vbox.addWidget(self.progressbar)
        vbox.addLayout(hbox1)
        self.setLayout(vbox)

    def find_clusters(self, n):
        self.number = 0
        try:
            self.number = int(n)
        except ValueError:
            self.number = 0
            return

        if self.number > len(self.audio_list):
            self.clusters_number_edit.setText(
                'Количество кластеров не должно быть больше количества песен')

        self.i = 0

        self.thread = AudioAnalysisThread(self)
        self.thread.start()

        self.thread.finished.connect(self.process_finished)
        self.thread.audio_processed.connect(self.change_progressbar)

    def change_progressbar(self):
        self.progressbar.setValue(self.i)
        self.i += 1

    def process_finished(self):
        self.progressbar.setValue(self.progressbar.maximum())
        self.clusters = clustering.clusters(
            self.audio_features_list, self.number)

        self.cluster_content_widget.clear()
        self.cluster_list_widget.clear()
        self.cluster_list_widget.addItems(
            map(str, list(range(0, len(self.clusters)))))

    def show_result(self):
        cluster_number = int(self.cluster_list_widget.currentItem().text())
        self.cluster_content_widget.clear()
        self.cluster_content_widget.addItems(
            [item.audio_file.name for item in self.clusters[cluster_number]])


class AudioAnalysisThread(QtCore.QThread):
    audio_processed = QtCore.pyqtSignal()
    finished = QtCore.pyqtSignal()

    def __init__(self, window):
        super().__init__()
        self.window = window

    def run(self):
        for audio in self.window.audio_list:
            if audio.meta.duration < 30.0:
                pass
            elif audio.path in self.window.window.AUDIO_FEATURES:
                self.window.audio_features_list.append(
                    self.window.window.AUDIO_FEATURES[audio.path])
            else:
                features = clustering.get_features(audio)
                self.window.window.AUDIO_FEATURES[audio.path] = features
                self.window.audio_features_list.append(features)
            self.audio_processed.emit()
        self.finished.emit()


def parse_args():
    parser = argparse.ArgumentParser(description='audioplayer')
    parser.add_argument(
        '-s', '--subdir', action='store_true', dest='subdirs',
        help='search in subdirectories')
    parser.add_argument('-d', '--directory', default=Path.home(),
                        help='music directory (default: home directory)')
    parser.add_argument('-f', '--formats', nargs='+', default=['mp3'],
                        help='required audio formats (default: mp3)')
    return parser.parse_args()


def main():
    args = parse_args()
    audio_files = files.find_audio_files(
        args.directory, args.subdirs, args.formats)

    app = QtWidgets.QApplication(sys.argv)
    album_win = PlayerWindow(audio_files)
    album_win.show()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()

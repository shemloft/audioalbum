import pygame
from pygame import mixer

ERROR_LOADING = 1


class MusicPlayer:
    def __init__(self, audio_files):
        mixer.init()
        mixer.music.set_volume(0.5)
        self.audio_files = audio_files
        self.is_pause = False
        self.current_audio = 0

    def get_cur_audio_file(self):
        return self.audio_files[self.current_audio]

    def play(self, audio_number):
        if self.is_pause:
            mixer.music.unpause()
            self.is_pause = False
            return 0
        try:
            song = self.audio_files[audio_number].path()
            mixer.music.load(song)
        except pygame.error:
            return ERROR_LOADING
        self.current_audio = audio_number
        mixer.music.play()
        return 0

    def play_next(self):
        self.is_pause = False
        return self.play((self.current_audio + 1) % len(self.audio_files))

    def play_previous(self):
        self.is_pause = False
        return self.play(
            (self.current_audio - 1 + len(self.audio_files))
            % len(self.audio_files))

    def pause(self):
        mixer.music.pause()
        self.is_pause = True

    def play_again(self):
        mixer.music.rewind()

    def change_volume(self, value):
        mixer.music.set_volume(value)

    def music_is_playing(self):
        return mixer.music.get_busy()

    def play_from_position(self, pos):
        if not self.music_is_playing():
            return
        mixer.music.rewind()
        mixer.music.play(0, pos)

    def stop(self):
        pygame.quit()
        mixer.quit()

    def restart(self):
        mixer.init()

import librosa
from collections import defaultdict
from sklearn.cluster import KMeans


def audio_features_generator(audio_files):
    for file in audio_files:
        yield AudioFileFeatures(file)


def get_audio_features_dict(audio_files):
    features_dict = {file: AudioFileFeatures(file) for file in audio_files}
    return features_dict


def get_features(audio_file):
    return AudioFileFeatures(audio_file)


def clusters(features_list, n):
    coordinates = [features.rms for features in features_list]

    kmeans = KMeans(n_clusters=n, n_init=20, max_iter=1000)
    res = kmeans.fit(coordinates)

    result_clusters = [[] for _ in range(n)]

    for i, features in enumerate(features_list):
        cluster_index = res.labels_[i]
        features.cluster_index = cluster_index
        result_clusters[cluster_index].append(features)

    return result_clusters


class AudioFileFeatures:
    def __init__(self, audio_file):
        self.audio_file = audio_file
        self.duration = self.audio_file.meta.duration
        self.cluster_index = -1
        self._extract_file_features()

    def _extract_file_features(self):
        y, sr = librosa.load(
            self.audio_file.path(), sr=10000, mono=True,
            offset=60.0 if self.duration > 90.0 else 0.0,
            duration=30.0, res_type='kaiser_fast')
        self.rms = librosa.feature.rmse(y=y)[0]

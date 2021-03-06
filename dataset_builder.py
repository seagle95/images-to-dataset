import logging
from pathlib import Path
from typing import Tuple, List

from sklearn.model_selection import KFold, StratifiedKFold, GroupKFold
import numpy as np
import pandas as pd

import utils
from stratified_group_k_fold import StratifiedGroupKFold


class DatasetBuilder:
    def __init__(self, data_root: Path, n_splits: int, with_shuffle: bool, with_stratify: bool, group: str,
                 metadata: Path, path_column: str, label_column: str, seed: int = None):
        self._data_root = data_root
        self._n_splits = n_splits
        self._with_shuffle = with_shuffle
        self._with_stratify = with_stratify
        self._group = group
        self._metadata = metadata
        self._path_column = path_column
        self._label_column = label_column
        self._seed = seed

    def build(self):
        paths, labels, groups = self._extract_paths_labels_groups()
        n_examples = len(paths)
        logging.info(f"{n_examples} examples have been found.")
        if n_examples > 0:
            return self._iter_dataset(paths, labels, groups)
        return []

    def _extract_paths_labels_groups(self) -> Tuple[List[Path], List[str], List[int]]:
        file_paths = []
        labels = []
        groups = []
        paths_labels_groups = None
        metadata = None

        if self._metadata is not None:
            metadata = pd.read_csv(self._metadata)
            if self._path_column in metadata:
                metadata[self._path_column] = metadata[self._path_column].apply(Path)
                if self._label_column in metadata:
                    path_existence = metadata[self._path_column].apply(Path.exists)
                    metadata = metadata.loc[path_existence]
                    metadata[self._label_column] = metadata[self._label_column].apply(str)
                    paths_labels_groups = metadata[[self._path_column, self._label_column]]

        if paths_labels_groups is None and self._data_root:
            paths_labels_groups = pd.DataFrame()
            for class_folder in utils.iter_folders(self._data_root):
                label = class_folder.name
                for file_path in utils.iter_files(class_folder):
                    if self.is_file_integral(file_path):
                        paths_labels_groups = paths_labels_groups.append(
                            {self._path_column: file_path, self._label_column: label}, ignore_index=True, sort=False)

        if paths_labels_groups is not None:
            if self._with_shuffle:
                paths_labels_groups = paths_labels_groups.sample(frac=1, replace=False, axis=0, random_state=self._seed)
            file_paths = paths_labels_groups[self._path_column].to_list()
            labels = paths_labels_groups[self._label_column].to_list()
            if self._group and metadata is not None and \
               all(c in metadata.columns for c in [self._path_column, self._group]):
                groups = metadata.set_index(self._path_column)\
                                 .loc[file_paths, self._group]

        return file_paths, labels, groups

    def is_file_integral(self, file_path: Path) -> bool:
        return True

    def _iter_dataset(self, file_paths: List[Path], labels: List[str], groups: List[int] = None):
        file_paths = np.array(file_paths)
        labels = np.array(labels)
        if groups is not None:
            groups = np.array(groups)
        if self._n_splits > 1:
            for p, (_, indices) in enumerate(self._split(file_paths, labels, groups)):
                yield self._iter_partition(file_paths[indices], labels[indices])
        else:
            np.random.seed(self._seed)
            indices = np.random.choice(np.arange(len(file_paths)), len(file_paths), replace=False)
            yield self._iter_partition(file_paths[indices], labels[indices])

    @staticmethod
    def _iter_partition(file_paths: np.array, labels: np.array):
        for path, label in zip(file_paths, labels):
            yield path, label

    def _split(self, file_paths: np.array, labels: np.array, groups: np.array = None):
        if self._with_stratify:
            if self._group and groups is not None:
                return StratifiedGroupKFold(n_splits=self._n_splits)\
                       .split(file_paths, labels, groups)
            else:
                return StratifiedKFold(n_splits=self._n_splits, shuffle=self._with_shuffle, random_state=self._seed) \
                       .split(file_paths, labels)
        else:
            if self._group and groups is not None:
                return GroupKFold(n_splits=self._n_splits) \
                       .split(file_paths, labels, groups)
            else:
                return KFold(n_splits=self._n_splits, shuffle=self._with_shuffle, random_state=self._seed) \
                       .split(file_paths, labels)

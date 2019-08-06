import numpy as np
import pandas as pd
from torch.utils.data import Dataset

"""
Represents the custom PPI dataset
"""


class PPIDataset(Dataset):

    def __init__(self, file_path, interaction_type=None):
        self._file_path = file_path
        # Read json
        data_df = pd.read_json(self._file_path)

        # Filter interaction types if required
        if interaction_type is not None:
            data_df = data_df.query('interactionType == "{}"'.format(interaction_type))

        # Filter features
        self._data_df = data_df[["normalised_abstract", "interactionType", "participant1Id", "participant2Id"]]

        # Set up labels
        self._labels = data_df[["isValid"]]
        self._labels = np.reshape(self._labels.values.tolist(), (-1,))

    def __len__(self):
        return self._data_df.shape[0]

    def __getitem__(self, index):
        return self._data_df.iloc[index, :], self._labels[index]

    @property
    def class_size(self):
        return 2

    @property
    def positive_label(self):
        return "yes"

    @property
    def feature_lens(self):
        return [250, 1, 1, 1]

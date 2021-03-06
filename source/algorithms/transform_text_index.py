import logging

import torch
from sklearn.feature_extraction.text import CountVectorizer

"""
Extracts vocab from data frame columns which have already been tokenised into words
"""


class TransformTextToIndex:

    def __init__(self, max_feature_lens, min_vocab_doc_frequency=5, case_insensitive=True, vocab_dict=None,
                 special_words=None, use_dataset_vocab=True):
        self.use_dataset_vocab = use_dataset_vocab
        self.case_insensitive = case_insensitive
        self.special_words = special_words or []
        self._vocab_dict = vocab_dict or {}

        self.max_feature_lens = max_feature_lens
        self.min_vocab_doc_frequency = min_vocab_doc_frequency

        # Load pretrained vocab

    @property
    def logger(self):
        return logging.getLogger(__name__)

    def construct_vocab_dict(self, data_loader):
        if self.use_dataset_vocab:
            vocab = self._get_vocab_dict(data_loader, self.get_specialwords_dict(),
                                         case_insensitive=self.case_insensitive,
                                         min_vocab_doc_frequency=self.min_vocab_doc_frequency)
        else:
            vocab = self.get_specialwords_dict()

        self.logger.info("Constructed vocab of size {}".format(len(vocab)))

        return vocab

    def get_specialwords_dict(self):
        """
        Ensure that the id of these words dont change
        :return:
        """
        tokens = [self.pad_token(), self.eos_token(), "PROTEIN1", "PROTEIN2", "PROTEIN_1",
                  "PROTEIN_2", self.UNK_token()]
        key_func = lambda x: x
        if self.case_insensitive:
            key_func = lambda x: x.lower()
        tokens_dict = {key_func(k): i for i, k in enumerate(tokens)}

        for k in self.special_words:
            if k not in tokens_dict:
                tokens_dict[k] = len(tokens_dict)

        return tokens_dict

    @staticmethod
    def pad_token():
        return "!@#"

    @staticmethod
    def eos_token():
        return "<EOS>"

    @staticmethod
    def UNK_token():
        return "<UNK>"

    @property
    def vocab_dict(self):
        return self._vocab_dict

    @vocab_dict.setter
    def vocab_dict(self, vocab_index):
        self._vocab_dict = vocab_index

    def fit(self, data_loader):
        if self._vocab_dict is None or len(self._vocab_dict) == 0:
            self._vocab_dict = self._get_vocab_dict(data_loader, self.get_specialwords_dict(), self.case_insensitive,
                                                    self.min_vocab_doc_frequency)

    @staticmethod
    def _get_vocab_dict(data_loader, special_words_dict, case_insensitive, min_vocab_doc_frequency):
        count_vectoriser = CountVectorizer(lowercase=case_insensitive, min_df=min_vocab_doc_frequency)
        f = lambda x: x
        if case_insensitive:
            f = lambda x: x.lower()

        # fit pad first so that it has index zero

        text = []
        for idx, b in enumerate(data_loader):
            b_x = b[0]

            column_text = []
            for c in b_x:
                column_text.extend(c)
            text.extend(column_text)

        count_vectoriser.fit(text)

        vocab_index_train = count_vectoriser.vocabulary_

        # Set up so that the special words index doesnt change
        final_dict = special_words_dict.copy()
        for k in vocab_index_train:
            if k not in final_dict:
                final_dict[k] = len(final_dict)

        return final_dict

    def transform(self, x):
        self.logger.info("Transforming TransformTextToIndex")
        f = lambda x: x
        if self.case_insensitive:
            f = lambda x: x.lower()

        tokeniser = CountVectorizer().build_tokenizer()
        pad_index = self._vocab_dict[f(self.pad_token())]
        unknown_index = self._vocab_dict[f(TransformTextToIndex.UNK_token())]
        batches = []
        unknown_words_count = 0
        for idx, b in enumerate(x):
            b_x = b[0]
            b_y = b[1]
            col = []
            for c_index, c in enumerate(b_x):
                row = []
                max = self.max_feature_lens[c_index]
                for _, r in enumerate(c):
                    tokens = [self._vocab_dict.get(f(w), unknown_index) for w in
                              tokeniser(r)][0:max]
                    tokens = tokens + [pad_index] * (max - len(tokens))
                    row.append(tokens)
                    # Unknown words count

                    unknown_words_count += sum(t == unknown_index for t in tokens)
                row = torch.Tensor(row).long()
                col.append(row)

            batches.append([col, b_y])

        self.logger.info("Total number of unknown occurances {}".format(unknown_words_count))

        self.logger.info("Completed TransformTextToIndex")
        return batches

    def fit_transform(self, data_loader):
        self.fit(data_loader)
        return self.transform(data_loader)

import collections
import os
from functools import lru_cache
from typing import List

import cv2
import numpy as np
import six
import unicodedata

from core.dto.enums import Device
from core.models.engines import OnnxBaseModel
from utils.logger import logger

_MODEL_INFO = {
    "ViT-B-16": {
        "struct": "ViT-B-16@RoBERTa-wwm-ext-base-chinese",
        "input_resolution": 224,
    },
    "ViT-L-14": {
        "struct": "ViT-L-14@RoBERTa-wwm-ext-base-chinese",
        "input_resolution": 224,
    },
    "ViT-L-14-336": {
        "struct": "ViT-L-14-336@RoBERTa-wwm-ext-base-chinese",
        "input_resolution": 336,
    },
    "ViT-H-14": {
        "struct": "ViT-H-14@RoBERTa-wwm-ext-large-chinese",
        "input_resolution": 224,
    },
    "RN50": {"struct": "RN50@RBT3-chinese", "input_resolution": 224},
}


@lru_cache()
def default_vocab():
    current_dir = os.path.dirname(__file__)
    return os.path.join(current_dir, "..", "configs", "clip_vocab.txt")


def convert_to_unicode(text):
    """Converts `text` to Unicode (if it's not already), assuming utf-8 input."""
    if six.PY3:
        if isinstance(text, str):
            return text
        elif isinstance(text, bytes):
            return text.decode("utf-8", "ignore")
        else:
            raise ValueError("Unsupported string type: %s" % (type(text)))
    else:
        raise ValueError("Not running on Python2 or Python 3?")


def load_vocab(vocab_file):
    """Loads a vocabulary file into a dictionary."""
    vocab = collections.OrderedDict()
    index = 0
    with open(vocab_file, "r", encoding="utf-8") as reader:
        while True:
            token = convert_to_unicode(reader.readline())
            if not token:
                break
            token = token.strip()
            vocab[token] = index
            index += 1
    return vocab


def whitespace_tokenize(text):
    """Runs basic whitespace cleaning and splitting on a piece of text."""
    text = text.strip()
    if not text:
        return []
    tokens = text.split()
    return tokens


def _is_punctuation(char):
    """Checks whether `chars` is a punctuation character."""
    cp = ord(char)
    # We treat all non-letter/number ASCII as punctuation.
    # Characters such as "^", "$", and "`" are not in the Unicode
    # Punctuation class, but we treat them as punctuation anyway, for
    # consistency.
    if (33 <= cp <= 47) or (58 <= cp <= 64) or (91 <= cp <= 96) or (123 <= cp <= 126):
        return True
    cat = unicodedata.category(char)
    if cat.startswith("P"):
        return True
    return False


def _is_control(char):
    """Checks whether `chars` is a control character."""
    # These are technically control characters, but we count them as whitespace
    # characters.
    if char == "\t" or char == "\n" or char == "\r":
        return False
    cat = unicodedata.category(char)
    if cat in ("Cc", "Cf"):
        return True
    return False


def _is_whitespace(char):
    """Checks whether `chars` is a whitespace character."""
    # \t, \n, and \r are technically control characters, but we treat them
    # as whitespace since they are generally considered as such.
    if char == " " or char == "\t" or char == "\n" or char == "\r":
        return True
    cat = unicodedata.category(char)
    if cat == "Zs":
        return True
    return False


def convert_by_vocab(vocab, items):
    """Converts a sequence of [tokens|ids] using the vocab."""
    output = []
    for item in items:
        output.append(vocab[item])
    return output


def convert_tokens_to_ids(vocab, tokens):
    return convert_by_vocab(vocab, tokens)


def convert_ids_to_tokens(inv_vocab, ids):
    return convert_by_vocab(inv_vocab, ids)


class ChineseClipONNX:
    """Ref: https://github.com/OFA-Sys/Chinese-CLIP"""

    def __init__(self, txt_model_path: str, img_model_path: str, model_arch: str, device: Device = Device.CPU, context_length: int = 52) -> None:
        # Load models
        self.txt_net = OnnxBaseModel(txt_model_path, device_type=device)
        self.img_net = OnnxBaseModel(img_model_path, device_type=device)
        # Image settings
        self.image_size = _MODEL_INFO[model_arch]["input_resolution"]
        # Text settings
        self._tokenizer = FullTokenizer()
        self.context_length = context_length

    def __call__(self, image: np.ndarray, text: List[str]):
        txt_features = self.txt_pipeline(text)
        img_features = self.img_pipeline(image)
        logits_per_image = 100 * np.dot(img_features, txt_features.T)
        probabilities = np.exp(logits_per_image) / np.sum(np.exp(logits_per_image), axis=1, keepdims=True)
        return probabilities

    def txt_pipeline(self, text: List[str]):
        text = self.tokenize(text, context_length=self.context_length)
        features = []
        for i in range(len(text)):
            blob = np.expand_dims(text[i], axis=0)
            feature = self.txt_net.get_ort_inference(blob)
            features.append(feature)
        features = np.squeeze(np.stack(features), axis=1)
        features = self.post_process(features)
        return features

    def img_pipeline(self, image: np.ndarray):
        blob = self.image_preprocess(image, image_size=self.image_size)
        outputs = self.img_net.get_ort_inference(blob)
        features = self.post_process(outputs)
        return features

    @staticmethod
    def normalize(data, mean, std):
        if not isinstance(mean, np.ndarray):
            mean = np.array(mean)
        if not isinstance(std, np.ndarray):
            std = np.array(std)
        _max = np.max(abs(data))
        _div = np.divide(data, _max)
        _sub = np.subtract(_div, mean)
        arrays = np.divide(_sub, std)
        arrays = np.transpose(arrays, (2, 0, 1)).astype(np.float32)
        return arrays

    def image_preprocess(self, image, image_size=224, bgr2rgb=False, mean_value=None, std_value=None):
        # Resize using OpenCV
        if mean_value is None:
            mean_value = [0.48145466, 0.4578275, 0.40821073]
        if std_value is None:
            std_value = [0.26862954, 0.26130258, 0.27577711]
        image_size = (image_size, image_size) if isinstance(image_size, int) else image_size
        image = cv2.resize(image, image_size)
        # Convert to RGB if needed
        if bgr2rgb:
            image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        # Convert to float and normalize
        image = self.normalize(image, mean_value, std_value)
        # [H W C] to [N C H W]
        image = np.expand_dims(image, 0)
        return image

    @staticmethod
    def post_process(outputs):
        return outputs / np.linalg.norm(outputs, axis=-1, keepdims=True)

    def tokenize(self, texts, context_length=52):
        """
        Returns the tokenized representation of given input string(s)
        Parameters
        ----------
        texts : Union[str, List[str]]
            An input string or a list of input strings to tokenize
        context_length : int
            The context length to use; all baseline models use 52 as the context length
        Returns
        -------
        A two-dimensional array containing the resulting tokens, shape = [number of input strings, context_length]
        """
        if isinstance(texts, str):
            texts = [texts]

        all_tokens = []
        for text in texts:
            tokenized_text = (
                    [self._tokenizer.vocab["[CLS]"]]
                    + self._tokenizer.convert_tokens_to_ids(self._tokenizer.tokenize(text))[: context_length - 2]
                    + [self._tokenizer.vocab["[SEP]"]]
            )
            all_tokens.append(tokenized_text)

        result = np.zeros((len(all_tokens), context_length), dtype=np.int64)

        for i, tokens in enumerate(all_tokens):
            if len(tokens) > context_length:
                logger.error(f"Truncating sequence {texts[i]} to {context_length} tokens")
            result[i, : len(tokens)] = np.array(tokens)

        return result


class BasicTokenizer(object):
    """Runs basic tokenization (punctuation splitting, lower casing, etc.)."""

    def __init__(self, do_lower_case=True):
        """Constructs a BasicTokenizer.

        Args:
          do_lower_case: Whether to lower case the input.
        """
        self.do_lower_case = do_lower_case

    def tokenize(self, text):
        """Tokenizes a piece of text."""
        text = convert_to_unicode(text)
        text = self._clean_text(text)

        # This was added on November 1st, 2018 for the multilingual and Chinese
        # models. This is also applied to the English models now, but it doesn't
        # matter since the English models were not trained on any Chinese data
        # and generally don't have any Chinese data in them (there are Chinese
        # characters in the vocabulary because Wikipedia does have some Chinese
        # words in the English Wikipedia.).
        text = self._tokenize_chinese_chars(text)

        orig_tokens = whitespace_tokenize(text)
        split_tokens = []
        for token in orig_tokens:
            if self.do_lower_case:
                token = token.lower()
                token = self._run_strip_accents(token)
            split_tokens.extend(self._run_split_on_punc(token))

        output_tokens = whitespace_tokenize(" ".join(split_tokens))
        return output_tokens

    @staticmethod
    def _run_strip_accents(text):
        """Strips accents from a piece of text."""
        text = unicodedata.normalize("NFD", text)
        output = []
        for char in text:
            cat = unicodedata.category(char)
            if cat == "Mn":
                continue
            output.append(char)
        return "".join(output)

    @staticmethod
    def _run_split_on_punc(text):
        """Splits punctuation on a piece of text."""
        chars = list(text)
        i = 0
        start_new_word = True
        output = []
        while i < len(chars):
            char = chars[i]
            if _is_punctuation(char):
                output.append([char])
                start_new_word = True
            else:
                if start_new_word:
                    output.append([])
                start_new_word = False
                output[-1].append(char)
            i += 1

        return ["".join(x) for x in output]

    def _tokenize_chinese_chars(self, text):
        """Adds whitespace around any CJK character."""
        output = []
        for char in text:
            cp = ord(char)
            if self._is_chinese_char(cp):
                output.append(" ")
                output.append(char)
                output.append(" ")
            else:
                output.append(char)
        return "".join(output)

    @staticmethod
    def _is_chinese_char(cp):
        """Checks whether CP is the codepoint of a CJK character."""
        # This defines a "chinese character" as anything in the CJK Unicode block:
        #   https://en.wikipedia.org/wiki/CJK_Unified_Ideographs_(Unicode_block)
        #
        # Note that the CJK Unicode block is NOT all Japanese and Korean characters,
        # despite its name. The modern Korean Hangul alphabet is a different block,
        # as is Japanese Hiragana and Katakana. Those alphabets are used to write
        # space-separated words, so they are not treated specially and handled
        # like the all the other languages.
        return ((0x4E00 <= cp <= 0x9FFF)
                or (0x3400 <= cp <= 0x4DBF)
                or (0x20000 <= cp <= 0x2A6DF)
                or (0x2A700 <= cp <= 0x2B73F)
                or (0x2B740 <= cp <= 0x2B81F)
                or (0x2B820 <= cp <= 0x2CEAF)
                or (0xF900 <= cp <= 0xFAFF)
                or (0x2F800 <= cp <= 0x2FA1F)
                )

    @staticmethod
    def _clean_text(text):
        """Performs invalid character removal and whitespace cleanup on text."""
        output = []
        for char in text:
            cp = ord(char)
            if cp == 0 or cp == 0xFFFD or _is_control(char):
                continue
            if _is_whitespace(char):
                output.append(" ")
            else:
                output.append(char)
        return "".join(output)


class WordpieceTokenizer(object):
    """Runs WordPiece tokenization."""

    def __init__(self, vocab, unk_token="[UNK]", max_input_chars_per_word=200):
        self.vocab = vocab
        self.unk_token = unk_token
        self.max_input_chars_per_word = max_input_chars_per_word

    def tokenize(self, text):
        """Tokenizes a piece of text into its word pieces.

        This uses a greedy longest-match-first algorithm to perform tokenization
        using the given vocabulary.

        For example:
          input = "tokenize"
                   tokenize
          output = ["to", "##ken", "##ize"]

        Args:
          text: A single token or whitespace separated tokens. This should have
            already been passed through `BasicTokenizer.

        Returns:
          A list of wordpiece tokens.
        """

        text = convert_to_unicode(text)

        output_tokens = []
        for token in whitespace_tokenize(text):
            chars = list(token)
            if len(chars) > self.max_input_chars_per_word:
                output_tokens.append(self.unk_token)
                continue

            is_bad = False
            start = 0
            sub_tokens = []
            while start < len(chars):
                end = len(chars)
                cur_substr = None
                while start < end:
                    substr = "".join(chars[start:end])
                    if start > 0:
                        substr = "##" + substr
                    if substr in self.vocab:
                        cur_substr = substr
                        break
                    end -= 1
                if cur_substr is None:
                    is_bad = True
                    break
                sub_tokens.append(cur_substr)
                start = end

            if is_bad:
                output_tokens.append(self.unk_token)
            else:
                output_tokens.extend(sub_tokens)
        return output_tokens


class FullTokenizer(object):
    """Runs end-to-end tokenization."""

    def __init__(self, vocab_file=default_vocab(), do_lower_case=True):
        self.vocab = load_vocab(vocab_file)
        self.inv_vocab = {v: k for k, v in self.vocab.items()}
        self.basic_tokenizer = BasicTokenizer(do_lower_case=do_lower_case)
        self.wordpiece_tokenizer = WordpieceTokenizer(vocab=self.vocab)

    def tokenize(self, text):
        split_tokens = []
        for token in self.basic_tokenizer.tokenize(text):
            for sub_token in self.wordpiece_tokenizer.tokenize(token):
                split_tokens.append(sub_token)

        return split_tokens

    def convert_tokens_to_ids(self, tokens):
        return convert_by_vocab(self.vocab, tokens)

    def convert_ids_to_tokens(self, ids):
        return convert_by_vocab(self.inv_vocab, ids)

    @staticmethod
    def convert_tokens_to_string(tokens, clean_up_tokenization_spaces=True):
        """Converts a sequence of tokens (string) in a single string."""

        def clean_up_tokenization(out_string):
            """Clean up a list of simple English tokenization artifacts
            like spaces before punctuations and abbreviated forms.
            """
            out_string = (
                out_string.replace(" .", ".")
                .replace(" ?", "?")
                .replace(" !", "!")
                .replace(" ,", ",")
                .replace(" ' ", "'")
                .replace(" n't", "n't")
                .replace(" 'm", "'m")
                .replace(" 's", "'s")
                .replace(" 've", "'ve")
                .replace(" 're", "'re")
            )
            return out_string

        text = " ".join(tokens).replace(" ##", "").strip()
        if clean_up_tokenization_spaces:
            clean_text = clean_up_tokenization(text)
            return clean_text
        else:
            return text

    def vocab_size(self):
        return len(self.vocab)

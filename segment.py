import os
from dataclasses import dataclass
from importlib import resources
from typing import List

from vnnlp import data


@dataclass
class FWObject:
    context: List[str]

    def __init__(self, check=False):
        self.context = [""] * 10
        if check:
            for i in range(0, 10, 2):
                self.context[i] = "<W>"
                self.context[i + 1] = "<T>"


@dataclass
class Node:
    condition: FWObject = None
    conclusion: str = None
    except_node: "Node" = None
    if_not_node: "Node" = None
    father_node: "Node" = None
    depth: int = 0

    def count_nodes(self) -> int:
        count = 1
        count = count + self.except_node.count_nodes() if self.except_node else count
        count = count + self.if_not_node.count_nodes() if self.if_not_node else count
        return count

    def satify(self, object: FWObject) -> bool:
        for i in range(10):
            key = self.condition.context[i]
            if key is not None and key != object.context[i]:
                return False
        return True


def get_concrete_value(string):
    if '""' in string:
        if "Word" in string:
            return "<W>"
        return "<T>"
    conclusion = string[string.find('"') + 1: len(string) - 1]
    return conclusion


vietnamese_word_normalizer = {
    "òa": "oà",
    "óa": "oá",
    "ỏa": "oả",
    "õa": "oã",
    "oạ": "oạ",
    "òe": "oè",
    "óe": "oé",
    "ỏe": "oẻ",
    "õe": "oẽ",
    "ọe": "oẹ",
    "úy": "uý",
    "ùy": "uỳ",
    "ủy": "uỷ",
    "ũy": "uỹ",
    "ụy": "uỵ",
    "Ủy": "Uỷ",
}

key_to_position_dict = {
    "tag": 0,
    "word": 1,
    "prevWord1": 2,
    "prevTag1": 3,
    "prevWord2": 4,
    "prevTag2": 5,
    "nextWord1": 6,
    "nextTag1": 7,
    "nextWord2": 8,
    "nextTag2": 9,
}


@dataclass
class WordTag:
    form: str
    word: str
    tag: str

    def __init__(self, form, tag):
        self.form = form
        self.tag = tag
        self.word = form.lower() if form else None


def get_condition(str_condition: str) -> FWObject:
    condition = FWObject(False)
    for rule in str_condition.split(" and "):
        rule = rule.rstrip()
        key = rule[rule.find(".") + 1: rule.find(" ")]
        value = get_concrete_value(rule)
        if key in key_to_position_dict:
            condition.context[key_to_position_dict[key]] = value
    return condition


def get_object(word_tags: List[WordTag], size: int, index: int):
    fw_object = FWObject(True)
    if index > 1:
        fw_object.context[4] = word_tags[index - 2].word
        fw_object.context[5] = word_tags[index - 2].tag
    if index > 0:
        fw_object.context[2] = word_tags[index - 1].word
        fw_object.context[3] = word_tags[index - 1].tag

    current_word = word_tags[index].word
    current_tag = word_tags[index].tag

    fw_object.context[0] = current_word
    fw_object.context[1] = current_tag
    if index < size - 1:
        fw_object.context[6] = word_tags[index + 1].word
        fw_object.context[7] = word_tags[index + 1].tag
    if index < size - 2:
        fw_object.context[8] = word_tags[index + 2].word
        fw_object.context[9] = word_tags[index + 2].tag
    return fw_object


import pickle5 as pickle
import logging


class Vocabulary:
    vn_dict = set()
    country_l_name = set()
    country_s_name = set()
    world_company = set()
    vn_locations = set()
    vn_first_sent_words = set()
    vn_middle_names = set()
    vn_family_names = set()

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        for dict_name in [
            "vn_dict",
            "country_l_name",
            "country_s_name",
            "world_company",
            "vn_locations",
            "vn_first_sent_words",
            "vn_middle_names",
            "vn_family_names",
        ]:
            try:
                with resources.open_binary(data, dict_name) as f:
                    setattr(self, dict_name, pickle.load(f))
            except:
                self.logger.error("Cannot set {}".format(dict_name), exc_info=True)


import re


class WordSegmenter:
    root: Node

    def __init__(self):
        self.vocabulary = Vocabulary()
        with resources.open_text(data, "word_segmenter.rdr") as f:
            lines = f.readlines()
            self.construct_tree_from_rule_file(lines)

    def construct_tree_from_rule_file(self, rule_file_content):
        self.root = Node(
            condition=FWObject(False),
            conclusion="NN",
            except_node=None,
            if_not_node=None,
            father_node=None,
            depth=0,
        )
        current_node = self.root
        current_depth = 0
        for line in rule_file_content:
            depth = 0
            for i in range(0, 7):
                if line[i] == "\t":
                    depth += 1
                else:
                    break
            line = line.rstrip()
            if not line:
                continue
            if "cc:" in line:
                continue
            splitted_tokens = line.split(" : ")
            condition = get_condition(splitted_tokens[0].rstrip())
            conclusion = get_concrete_value(splitted_tokens[1].rstrip())
            new_node = Node(
                condition=condition,
                conclusion=conclusion,
                except_node=None,
                if_not_node=None,
                father_node=None,
                depth=depth,
            )
            if depth > current_depth:
                current_node.except_node = new_node
            elif depth == current_depth:
                current_node.if_not_node = new_node
            else:
                while current_node.depth != depth:
                    current_node = current_node.father_node
                current_node.if_not_node = new_node
            new_node.father_node = current_node
            current_node = new_node
            current_depth = depth

    def get_initial_segmentation(self, sentence: str):
        word_tags = []
        for regexp, replaced_value in vietnamese_word_normalizer.items():
            sentence.replace(regexp, replaced_value)
        tokens = re.split("\\s+", sentence)
        lower_tokens = re.split("\\s+", sentence.lower())
        i = 0
        while i < len(tokens):
            token = tokens[i]
            if all(character.isalpha() for character in token):
                if (
                        token[0].islower()
                        and (i + 1) < len(tokens)
                        and tokens[i + 1][0].isupper()
                ):
                    word_tags.append(WordTag(token, "B"))
                    i += 1
                    continue

                is_single_syllable = True
                for j in range(min(i + 4, len(tokens)), i + 1, -1):
                    word = " ".join(lower_tokens[i:j])
                    if (
                            word in self.vocabulary.vn_dict
                            or word in self.vocabulary.vn_locations
                            or word in self.vocabulary.country_l_name
                    ):
                        word_tags.append(WordTag(token, "B"))
                        for k in range(i + 1, j):
                            word_tags.append(WordTag(tokens[k], "I"))
                        i = j - 1
                        is_single_syllable = False
                        break
                if is_single_syllable:
                    lower_cased_token = lower_tokens[i]
                    if (
                            lower_cased_token in self.vocabulary.vn_first_sent_words
                            or token[0].islower()
                            or all(character.isupper() for character in token)
                            or lower_cased_token in self.vocabulary.country_s_name
                            or lower_cased_token in self.vocabulary.world_company
                    ):
                        word_tags.append(WordTag(token, "B"))
                        i += 1
                        continue
                    i_lower = i + 1
                    for i_lower in range(i + 1, min(i + 4, len(tokens))):
                        n_token = tokens[i_lower]
                        if (
                                n_token[0].islower()
                                or not all(character.isalpha() for character in n_token)
                                or n_token == "LBKT"
                                or n_token == "RBKT"
                        ):
                            break
                    if i_lower > i + 1:
                        is_not_middlename = True
                        if (
                                lower_cased_token in self.vocabulary.vn_middle_names
                                and i >= 1
                        ):
                            prev_t = tokens[i - 1]
                            if (
                                    prev_t[0].isupper()
                                    and prev_t.lower() in self.vocabulary.vn_family_names
                            ):
                                word_tags.append(WordTag(token, "I"))
                                is_not_middlename = False
                        if is_not_middlename:
                            word_tags.append(WordTag(token, "B"))
                        for k in range(i + 1, i_lower):
                            word_tags.append(WordTag(tokens[k], "I"))
                        i = i_lower - 1
                    else:
                        word_tags.append(WordTag(token, "B"))
            else:
                word_tags.append(WordTag(token, "B"))
            i += 1
        return word_tags

    def find_fired_node(self, object: FWObject) -> Node:

        current_node = self.root
        fired_node = None
        while True:
            if current_node.satify(object):
                fired_node = current_node
                if current_node.except_node is None:
                    break
                else:
                    current_node = current_node.except_node
            else:
                if current_node.if_not_node is None:
                    break
                else:
                    current_node = current_node.if_not_node
        return fired_node

    def segment_string_to_token(self, string: str):
        string = re.sub(r"(\S)([,.])", r"\1 \2", string)
        line = string.rstrip()
        if not line:
            return os.linesep
        word_tags: List[WordTag] = self.get_initial_segmentation(line)
        current_token = ""
        results = []
        for word_tag in word_tags:
            if word_tag.tag == 'I':
                current_token = '_'.join([current_token, word_tag.form])
            elif word_tag.tag == 'B':
                if current_token:
                    results.append(current_token)
                current_token = word_tag.form
        if current_token:
            results.append(current_token)
        return results

    def segment_tokenized_string(self, string: str):
        result = ""
        string = re.sub(r"(\S)([,.])", r"\1 \2", string)
        line = string.rstrip()
        if not line:
            return None
        word_tags: List[WordTag] = self.get_initial_segmentation(line)
        size = len(word_tags)
        for i, word_tag in enumerate(word_tags):
            object = get_object(word_tags, size, i)
            fired_node = self.find_fired_node(object)
            if fired_node and fired_node.depth > 0:
                if fired_node.conclusion == "B":
                    result += " " + word_tag.form
                else:
                    result += "_" + word_tag.form
            else:
                if word_tag.tag == "B":
                    result += " " + word_tag.form
                else:
                    result += "_" + word_tag.form
        return result.strip()


#
# y_ = "Ông Nguyễn Khắc Chúc đang làm việc tại Đại học Quốc gia Hà Nội. Bà Lan, vợ ông Chúc, cũng làm việc tại đây. Nếu có ước muốn cho cuộc đời, hãy nhớ ước muốn cho thời gian trở lại"
# y_ = "Tôn Ngộ Không phò Đường Tăng đi thỉnh kinh tại Tây Trúc"
# segmenter = WordSegmenter()
# for string in y_.split("."):
#     print(segmenter.segment_string_to_token(string.strip()))

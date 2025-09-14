import re
import sys
from os.path import abspath, dirname
import numpy as np
import spacy
from spacy.matcher import Matcher
from sklearn.metrics.pairwise import cosine_similarity

# add the reproduction_utils dir to system path in order to find the other modules when running from other directory
sys.path.append(dirname(abspath(__file__)))
from llm_helper import get_embedding

nlp = spacy.load("en_core_web_lg")

def clean_word(word: str):
    stop_words = ['the', 'a', 'an', 'in', 'on', 'at', "to", "with","button",'of','or']
    word = " ".join([i for i in word.split() if i not in stop_words])
    word = word.replace("\"", '').replace("\'", '').replace("`", "").replace("+", "add").replace("menuview", "menu view").lstrip(" ").rstrip(" ")
    return word

def get_word_similarity_gpt(word_a, word_b):
    embed_a = np.array(get_embedding(word_a))
    embed_b = np.array(get_embedding(word_b))
    return cosine_similarity([embed_a], [embed_b])[0][0]

def get_word_similarity(word_a, word_b):
    word_a = clean_word(word_a.lower())
    word_b = clean_word(word_b.lower())
    if word_a == "" or word_b == "":
        return 0
    # if word_a in word_b or word_b in word_a:
    #     return 1
    if word_a == word_b: # a and b may not have vector representation
        return 1
    word_a_token = nlp(word_a)
    word_a_token_lemma = nlp(" ".join([_.lemma_ for _ in word_a_token]))
    word_b_token = nlp(word_b)
    word_b_token_lemma = nlp(" ".join([_.lemma_ for _ in word_b_token]))
    orig_form_sim = 0
    if word_a_token.vector_norm and word_b_token.vector_norm:
        orig_form_sim = max(word_a_token.similarity(word_b_token), 0)  # to avoid return negative cosine similarity
    lemma_form_sim = 0
    if word_a_token_lemma.vector_norm and word_b_token_lemma.vector_norm:
        lemma_form_sim = max(word_a_token_lemma.similarity(word_b_token_lemma), 0)
    return max(orig_form_sim, lemma_form_sim)


def camel_case_split(str):
    return ' '.join(re.findall(r'[A-Z](?:[a-z]+|[A-Z]*(?=[A-Z]|$))', str))


def normalize_res_id(res_id):
    res_name = res_id.split("/")[-1]
    if '_' in res_id:
        return res_name.replace("_", ' ')
    if any([i.isupper() for i in res_id]):
        return camel_case_split(res_name)
    return res_name

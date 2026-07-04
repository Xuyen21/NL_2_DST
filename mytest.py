import spacy

from evaluations.scoring.helpers import count_primitive_kv_pairs

SYSTEM_PROMPT = """You are a knowledgeable assistant specialized in
recognizing and understanding named entities
and their interrelations . If requested to
organize information in tabular format , you are
adept at filtering and presenting only the
relevant and valid results . You will exclude
any results that are not pertinent or are
inaccurate from the table according to the
discussion history ."""

a = None
b = 'something'

if a and not b:
     print()
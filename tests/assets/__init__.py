import os
import json

__all__ = ['TEXT', 'QUOTES']

assets_dir = os.path.dirname(__file__)

with open(os.path.join(assets_dir, 'data.json'), 'r', encoding='utf-8') as fp:
    data = json.load(fp)

TEXT = ''.join(data['text'])
QUOTES = data['quotes']

# -*- coding: utf-8 -*-
"""New torchtext.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1OdZtTLBeoqD1EmPv2KnZ5CqkaKLnUSPI
"""

# import torch
# from torchtext.datasets import AG_NEWS
# # !pip install torchdata

# train_iter = iter(AG_NEWS(split='train'))

# next(train_iter)

# from torchtext.data.utils import get_tokenizer
# from torchtext.vocab import build_vocab_from_iterator

# # iterator for the data
# train_iter = AG_NEWS(split='train')

# def yield_tokens(data_iter):
#   for label, text in data_iter:
#     yield tokenizer(text)

# # creates tokenizer
# tokenizer = get_tokenizer('basic_english')

# # builds vocab by using tokenizer on data iterator
# vocab = build_vocab_from_iterator(yield_tokens(train_iter), specials=['<unk>'])
# vocab.set_default_index(vocab['<unk>'])

# next(iter(train_iter))

# # vocab(['hello', 'my', 'dear'])
# # vocab.get_stoi()

# ''' 
# OLD:
# 1. Get tokenizer
# 2. Create field
# 3. Create Dataset
# 4. Build vocabulary
# 5. Build data (tensor) iterator

# NEW:
# 1. Create data (text) iterator
# 2. Get tokenizer
# 3. Build vocabulary (w/ tokenizer and data iterator)
# 4. Create data processor (w/ vocabulary and tokenizer)
# 5. Create data (tensor) iterator (w/ data iterator and data processor)
# '''

# # numericalizer for data loader
# text_pipeline = lambda x: vocab(tokenizer(x))
# label_pipeline = lambda x : int(x) - 1

# from torch.utils.data import DataLoader
# from torch import tensor

# device = 'cuda' if torch.cuda.is_available() else 'cpu'

# def collate_batch(batch):
#   label_list, text_list, offsets = [], [], [0]
#   for label, text in batch:
#     label_list.append(label_pipeline(label))
#     processed_text = tensor(text_pipeline(text), dtype=torch.int64)
#     text_list.append(processed_text)
#     offsets.append(processed_text.size(0))
#   label_list = torch.tensor(label_list, dtype=torch.int64)
#   offsets = torch.tensor(offsets)[:-1].cumsum(dim=0)
#   # text_list = torch.cat(text_list)
#   text_list = torch.nn.utils.rnn.pad_sequence(text_list, padding_value=0)
#   print(type(text_list))
#   return label_list.to(device), text_list.to(device), offsets.to(device)


# dataloader = DataLoader(train_iter, batch_size=8, shuffle=True, collate_fn=collate_batch)

# output = next(iter(dataloader))

# output[1].shape

# output

import torch
from torchtext.datasets import AG_NEWS
from torchtext.data.utils import get_tokenizer
from torchtext.vocab import build_vocab_from_iterator
from torch.utils.data import DataLoader

# data processing block

# tokenizer
tokenizer = get_tokenizer('basic_english')

# data iterator
train_iter = AG_NEWS(split='train')

# vocabulary
def yield_tokens(iterator):
  for label, text in iterator:
    yield tokenizer(text)
vocab = build_vocab_from_iterator(yield_tokens(train_iter), min_freq=2, max_tokens=10000, specials=['<unk>'])
vocab.set_default_index(vocab['<unk>'])

# helper functions for collate_fn
def text_pipeline(text):
  return vocab(tokenizer(text))

def label_pipeline(label):
  return int(label) - 1

# collate_fn
def collate_fn(batch):
  labels, texts = [], []
  for label, text in batch:
    labels.append(label_pipeline(label))
    texts.append(torch.tensor(text_pipeline(text), dtype=torch.int64))
  texts = torch.nn.utils.rnn.pad_sequence(texts)
  return texts, labels

# data loader
data_loader = DataLoader(train_iter, batch_size=8, collate_fn=collate_fn, shuffle=False)

output = next(iter(data_loader))

output


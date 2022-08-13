# -*- coding: utf-8 -*-
"""NLP Synthesis 3.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1vWfEptsHmwEAJwXzKKdWGPMEVWKISlZo
"""

import torch
import torch.nn.functional as F
import torchtext
import torch.nn as nn
from torchtext.vocab import build_vocab_from_iterator
from torchtext.data.utils import get_tokenizer
from torch.utils.data import DataLoader, Dataset
import time
import random
import pandas as pd
from sklearn.model_selection import train_test_split

!wget https://github.com/rasbt/python-machine-learning-book-3rd-edition/raw/master/ch08/movie_data.csv.gz
!gunzip -f movie_data.csv.gz

# # data processing block
# df = pd.read_csv('movie_data.csv')

# # create train/val split
# xtrain, xval, ytrain, yval = train_test_split(df['review'].tolist(), df['sentiment'].tolist(), test_size=0.2)

# # create dataset
# train_data = list(zip(xtrain, ytrain))
# val_data = list(zip(xval, yval))

# # sort dataset based on string length (no point because data loader shuffles in the end)
# train_data.sort(key=lambda x: len(x[0]))
# val_data.sort(key=lambda x: len(x[0]))

# # create tokenizer
# tokenizer = get_tokenizer('basic_english')

# # build vocabulary
# def yield_tokens(iterator):
#   for text, _ in iterator:
#     yield tokenizer(text)

# vocab = build_vocab_from_iterator(yield_tokens(train_data), specials=['<unk>', '<pad>'], max_tokens=10000, min_freq=2)
# vocab.set_default_index(vocab['<unk>'])

# # helper functions
# def text_pipeline(text):
#   return vocab(tokenizer(text))

# # collate_fn
# def collate_fn(batch):
#   text_list, label_list = [], []
#   for text, label in batch:
#     text_list.append(torch.tensor(text_pipeline(text), dtype=torch.int64))
#     label_list.append(label)
#   text_list = torch.nn.utils.rnn.pad_sequence(text_list)
#   label_list = torch.tensor(label_list, dtype=torch.int64)
#   return text_list, label_list

# # data loader
# train_loader = DataLoader(train_data, batch_size=64, collate_fn=collate_fn, shuffle=False)
# val_loader = DataLoader(val_data, batch_size=64, collate_fn=collate_fn, shuffle=False)

# test = iter(train_loader)
# for i in range(1000):
#   print(next(test)[0].shape)

# data processing block #2
df = pd.read_csv('movie_data.csv')

# create train/val split
xtrain, xval, ytrain, yval = train_test_split(df['review'].tolist(), df['sentiment'].tolist(), test_size=0.2)

# create dataset
train_data = list(zip(xtrain, ytrain))
val_data = list(zip(xval, yval))

# sort dataset based on string length (no point because data loader shuffles in the end)
train_data.sort(key=lambda x: len(x[0]))
val_data.sort(key=lambda x: len(x[0]))

# create tokenizer
tokenizer = get_tokenizer('basic_english')

# build vocabulary
def yield_tokens(iterator):
  for text, _ in iterator:
    yield tokenizer(text)

vocab = build_vocab_from_iterator(yield_tokens(train_data), specials=['<unk>', '<pad>'], max_tokens=10000, min_freq=2)
vocab.set_default_index(vocab['<unk>'])

# helper functions
def text_pipeline(text):
  return vocab(tokenizer(text))

class IMDBDataset(Dataset):
  def __init__(self, data):
    super().__init__()
    

# collate_fn
def collate_fn(batch):
  text_list, label_list = [], []
  for text, label in batch:
    text_list.append(torch.tensor(text_pipeline(text), dtype=torch.int64))
    label_list.append(label)
  text_list = torch.nn.utils.rnn.pad_sequence(text_list)
  label_list = torch.tensor(label_list, dtype=torch.int64)
  return text_list, label_list

# data loader
train_loader = DataLoader(train_data, batch_size=64, collate_fn=collate_fn, shuffle=False)
val_loader = DataLoader(val_data, batch_size=64, collate_fn=collate_fn, shuffle=False)

next(iter(train_loader))[1]

# RNN block
class RNN(nn.Module):
  def __init__(self, input_dim, embedding_dim, hidden_dim, output_dim):
    super().__init__()

    self.embedding = nn.Embedding(input_dim, embedding_dim)
    self.rnn = nn.LSTM(embedding_dim, hidden_dim, bidirectional=True)
    self.combine = nn.Linear(hidden_dim * 2, hidden_dim)
    self.fc = nn.Linear(hidden_dim, output_dim)

  def forward(self, text):
    embedded = self.embedding(text)

    _, (hidden, cell) = self.rnn(embedded)
    hidden = self.combine(torch.cat((hidden[0:1], hidden[1:2]), dim=2))
    cell = self.combine(torch.cat((cell[0:1], cell[1:2]),dim=2))

    hidden.squeeze_(0)
    output = self.fc(hidden)
    return output

# training set-up block
device = 'cuda' if torch.cuda.is_available() else 'cpu'
epochs = 15
batch_size = 128
lr = 0.01
input_dim = len(vocab)
embedding_dim = 128
hidden_dim = 256
num_classes = 2

model = RNN(input_dim, embedding_dim, hidden_dim, num_classes).to(device)
optimizer = torch.optim.Adam(model.parameters(), lr=lr)
loss_fn = nn.CrossEntropyLoss()

def compute_accuracy(data_loader):
  with torch.no_grad():
    correct, total = 0, 0
    for features, targets in data_loader:
      features = features.to(device)
      targets = targets.to(device)
      output = model(features)
      predicted = output.argmax(1)

      total += targets.size(0)
      correct += (predicted == targets).sum()
    return 100 * correct.float() / total

# training block
start_time = time.time()
model.train()
for epoch in range(epochs):
  for i, (text, labels) in enumerate(train_loader):
    text = text.to(device)
    labels = labels.to(device)

    output = model(text)
    loss = loss_fn(output, labels)
    optimizer.zero_grad()
    loss.backward()
    torch.nn.utils.clip_grad_norm_(model.parameters(), max_norm=1)
    optimizer.step()

    if i % 300 == 0:
      model.eval()
      print(f'Epoch: {epoch + 1:03d} / {epochs:03d} | Batch: {i:03} / {len(train_loader):03d} | Loss: {loss:.4f}')

      with torch.no_grad():
        print(f'Training Accuracy: {compute_accuracy(train_loader):.2f}%')
        print(f'Valid Accuracy: {compute_accuracy(val_loader):.2f}%')
      model.train()


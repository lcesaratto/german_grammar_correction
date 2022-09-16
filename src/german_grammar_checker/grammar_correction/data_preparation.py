import pandas as pd
from transformers import BertTokenizer
import torch
from tqdm import tqdm
from torch.utils.data import TensorDataset, DataLoader


class DataPreparator:
    def __init__(self, model_name, batch_size):
        self.tokenizer = BertTokenizer.from_pretrained(model_name)
        # print(self.tokenizer.all_special_tokens)
        # print(self.tokenizer.all_special_ids)
        self.batch_size = batch_size
        self.token_classes = {"die": 1,
                              "der": 2,
                              "das": 3,
                              "den": 4,
                              "dem": 5,
                              "des": 6,
                              "Die": 7,
                              "Der": 8,
                              "Das": 9,
                              "Den": 10,
                              "Dem": 11,
                              "Des": 12, }
        self.classes_ids = {0: 0,
                            1: self.tokenizer.convert_tokens_to_ids("die"),
                            2: self.tokenizer.convert_tokens_to_ids("der"),
                            3: self.tokenizer.convert_tokens_to_ids("das"),
                            4: self.tokenizer.convert_tokens_to_ids("den"),
                            5: self.tokenizer.convert_tokens_to_ids("dem"),
                            6: self.tokenizer.convert_tokens_to_ids("des"),
                            7: self.tokenizer.convert_tokens_to_ids("Die"),
                            8: self.tokenizer.convert_tokens_to_ids("Der"),
                            9: self.tokenizer.convert_tokens_to_ids("Das"),
                            10: self.tokenizer.convert_tokens_to_ids("Den"),
                            11: self.tokenizer.convert_tokens_to_ids("Dem"),
                            12: self.tokenizer.convert_tokens_to_ids("Des"), }

    def _load_dataset(self, data_path) -> pd.DataFrame:
        return pd.read_csv(data_path, nrows=None)

    def _prepare_data(self, df: pd.DataFrame) -> pd.DataFrame:
        df = df[["masked_sentence", "wrong_sentence", "masked_token"]]
        return df

    def _create_tensors(self, df: pd.DataFrame):
        wrong_sentences = df["wrong_sentence"].values
        masked_sentences = df["masked_sentence"].values
        masked_tokens = df["masked_token"].replace(
            self.token_classes).to_list()

        input_ids = []
        attention_masks = []
        print("\nTokenizing training data...")
        for sent in tqdm(wrong_sentences):
            encoded_dict = self.tokenizer(
                sent,
                truncation=True,
                max_length=128,
                padding='max_length',
                return_attention_mask=True,
                return_tensors='pt',
            )
            input_ids.append(encoded_dict['input_ids'])
            attention_masks.append(encoded_dict['attention_mask'])

        input_ids = torch.cat(input_ids, dim=0)
        attention_masks = torch.cat(attention_masks, dim=0)

        labels = []
        print("\nTokenizing labels...")
        for sent in tqdm(masked_sentences):
            encoded_dict = self.tokenizer(
                sent,
                truncation=True,
                max_length=128,
                padding='max_length',
                return_attention_mask=False,
                return_tensors='pt',
            )
            labels.append(encoded_dict['input_ids'])

        labels = torch.cat(labels, dim=0)
        labels = labels * (labels == 5)
        labels = (labels / 5) * torch.tensor(masked_tokens).view(-1, 1)
        labels = labels.type(torch.LongTensor)

        return input_ids, attention_masks, labels

    def _create_dataloader(self, input_ids, attention_masks, labels):
        dataset = TensorDataset(input_ids, attention_masks, labels)
        dataloader = DataLoader(dataset, shuffle=False,
                                batch_size=self.batch_size)

        return dataloader

    def get_dataloaders(self, data_path):
        df = self._load_dataset(data_path)
        df = self._prepare_data(df)
        input_ids, attention_masks, labels = self._create_tensors(df)
        dataloader = self._create_dataloader(
            input_ids, attention_masks, labels)

        return dataloader

    def get_sentence_dataloader(self, sentence):
        encoded_dict = self.tokenizer(
            sentence,
            truncation=True,
            max_length=128,
            padding='max_length',
            return_attention_mask=True,
            return_tensors='pt',
        )
        input_ids = [encoded_dict['input_ids']]
        attention_masks = [encoded_dict['attention_mask']]
        input_ids = torch.cat(input_ids, dim=0)
        attention_masks = torch.cat(attention_masks, dim=0)

        dataset = TensorDataset(input_ids, attention_masks)
        dataloader = DataLoader(dataset, shuffle=False,
                                batch_size=self.batch_size)
        return dataloader
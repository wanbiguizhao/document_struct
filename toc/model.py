# main.py
# ! pip install torchvision
from typing import Any
from lightning.pytorch.utilities.types import STEP_OUTPUT
import torch, torch.nn as nn, torch.utils.data as data, torchvision as tv, torch.nn.functional as F
import lightning as L
from transformers.models.bert import BertModel
# --------------------------------
# Step 1: Define a LightningModule
# --------------------------------
# A LightningModule (nn.Module subclass) defines a full *system*
# (ie: an LLM, diffusion model, autoencoder, or simple image classifier).


class TableOfContentModel(L.LightningModule):
    """
    现在的大致思路是：
    1. 把版面分析识别出来的每一个block变成句子向量
    2. 句子向量进过bert输出变成特征向量
    3. 特征向量经过softmax变成大纲级别。
    bert是具备动态预测级别的能力的。
    """
    def __init__(self, bert:BertModel,toc_max_depth,feat_dim,*args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.bert=bert # 利用bert的attention机制，
        self.toc_max_depth=toc_max_depth
        self.feat_dim=feat_dim
        # bert attention之后进行两次dense，然后进行分类。
        self.toc_cls=nn.Sequential(
            nn.Linear(self.feat_dim, self.feat_dim//2),
            nn.Tanh(),
            nn.Linear(self.feat_dim//2, len(self.toc_max_depth)) 
        )

    def forward(self, feats, feats_mask, ly_cls_labels=None, ly_labels_mask=None):
        bert_feats=self.bert(inputs_embeds=feats,attention_mask=feats_mask)
        toc_feature=self.toc_cls(bert_feats)
        toc_cls_preds = torch.argmax(toc_feature, dim=-1).detach() 
        return toc_cls_preds

    def training_step(self, batch) -> STEP_OUTPUT:
        x,y=batch
        x=x.view(x.size(0), -1)
        z=self.bert(x)
        z=self.toc_cls(z)
        loss=F.mse_loss(z,y)
        return loss
    
    def configure_optimizers(self):
        optimizer = torch.optim.Adam(self.parameters(), lr=1e-3)
        return optimizer


class LitAutoEncoder(L.LightningModule):
    def __init__(self):
        super().__init__()
        self.encoder = nn.Sequential(nn.Linear(28 * 28, 128), nn.ReLU(), nn.Linear(128, 3))
        self.decoder = nn.Sequential(nn.Linear(3, 128), nn.ReLU(), nn.Linear(128, 28 * 28))

    def forward(self, x):
        # in lightning, forward defines the prediction/inference actions
        embedding = self.encoder(x)
        return embedding

    def training_step(self, batch, batch_idx):
        # training_step defines the train loop. It is independent of forward
        x, y = batch
        x = x.view(x.size(0), -1)
        z = self.encoder(x)
        x_hat = self.decoder(z)
        loss = F.mse_loss(x_hat, x)
        self.log("train_loss", loss)
        return loss

    def configure_optimizers(self):
        optimizer = torch.optim.Adam(self.parameters(), lr=1e-3)
        return optimizer


# -------------------
# Step 2: Define data
# -------------------
dataset = tv.datasets.MNIST(".", download=True, transform=tv.transforms.ToTensor())
train, val = data.random_split(dataset, [55000, 5000])

# -------------------
# Step 3: Train
# -------------------
autoencoder = LitAutoEncoder()
trainer = L.Trainer()
trainer.fit(autoencoder, data.DataLoader(train), data.DataLoader(val))
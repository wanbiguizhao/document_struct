# main.py
# ! pip install torchvision
from typing import Any, Optional
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
        self.lstm=nn.LSTM(feat_dim,feat_dim//4,bidirectional=True)
        
        self.toc_cls=nn.Sequential(
            nn.Linear(self.feat_dim//2, self.feat_dim//8),
            nn.Tanh(),
            nn.Linear(self.feat_dim//8, self.toc_max_depth) 
        )
        

    def forward(self, feats, feats_mask, ly_cls_labels=None, ly_labels_mask=None):
        bert_feats,pooled_output=self.bert(inputs_embeds=feats,attention_mask=feats_mask)
        lstm_feature, (h,c)=self.lstm(bert_feats)
        hidden = torch.cat((lstm_feature[:,-1, :self.feat_dim//4],lstm_feature[:,0, self.feat_dim//4:]),dim=-1)
        toc_feature=self.toc_cls(hidden)
        toc_cls_preds = torch.argmax(toc_feature, dim=-1).detach() 
        return toc_cls_preds

    def validation_step(self, batch, batch_idx) -> STEP_OUTPUT :
        #batch,attention_mask=batch
        x,y,attention_mask=batch
        bert_feats=self.bert(inputs_embeds=x,attention_mask=attention_mask)[0]
        lstm_feature, (h,c)=self.lstm(bert_feats)
        #hidden = torch.cat((lstm_feature[:,-1, :self.feat_dim//4],lstm_feature[:,0, self.feat_dim//4:]),dim=-1)
        z=self.toc_cls(lstm_feature)
        loss=F.cross_entropy(z.permute(0,2,1),y,weight=torch.tensor([0.1,0.25,0.35,0.3],dtype=torch.float))
        #print(loss)
        print({'val_loss': loss,"m":torch.sum(torch.argmax(z,dim=-1)==y)/y.numel(),"origin":torch.sum(y==torch.zeros_like(y))/y.size(-1)})
        return {'val_loss': loss}
    
    def training_step(self, batch) -> STEP_OUTPUT:
        x,y,attention_mask=batch
        bert_feats=self.bert(inputs_embeds=x,attention_mask=attention_mask)[0]
        lstm_feature, (h,c)=self.lstm(bert_feats)
        z=self.toc_cls(lstm_feature)
        loss=F.cross_entropy(z.permute(0,2,1),y,weight=torch.tensor([0.1,0.25,0.35,0.3],dtype=torch.float),size_average=True)
        #print(loss)
        self.log("train_loss",loss)
        self.log("acc",torch.sum(torch.argmax(z,dim=-1)==y)/y.numel())
        return loss
    
    def configure_optimizers(self):
        optimizer = torch.optim.Adam(self.parameters(), lr=1e-4)
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


# # -------------------
# # Step 2: Define data
# # -------------------
# dataset = tv.datasets.MNIST(".", download=True, transform=tv.transforms.ToTensor())
# train, val = data.random_split(dataset, [55000, 5000])

# # -------------------
# # Step 3: Train
# # -------------------
# autoencoder = LitAutoEncoder()
# trainer = L.Trainer()
# trainer.fit(autoencoder, data.DataLoader(train), data.DataLoader(val))

if __name__=="__main__":
    from transformers import AutoTokenizer, AutoModel
    from transformers.models import bert
    from tokenizers import Tokenizer

    bert_config=bert.BertConfig.from_pretrained("/home/liukun/share/bert-finance-L-12_H-768_A-12_pytorch/")#.from_pretrained("/home/liukun/share/bert-finance-L-12_H-768_A-12_pytorch")
    bert_config.num_hidden_layers=3
    bert=bert.BertModel(bert_config)
    #bert=bert.BertModel.from_pretrained("/home/liukun/share/bert-finance-L-12_H-768_A-12_pytorch/")
    # import torch 
    # test_tensor=torch.randn(25,40,768)
    # x=bert(inputs_embeds=test_tensor) 
    # print(x[0].shape)
    # toc_model=TableOfContentModel(bert,7,768)
    # y=toc_model(test_tensor,None)
    # print(y[0])
    from dataset import toc_ds,collate_func
    train, val = data.random_split(toc_ds, [46,13])
    autoencoder = TableOfContentModel(bert,4,768)
    trainer = L.Trainer(accelerator="cpu",devices=1,log_every_n_steps=20,val_check_interval=1.0)
    trainer.fit(autoencoder, data.DataLoader(train,collate_fn=collate_func,batch_size=2), data.DataLoader(val,batch_size=5,collate_fn=collate_func))
    
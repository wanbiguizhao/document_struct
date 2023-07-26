from torch.utils.data import Dataset
import torch
import os 
# from text2vec import SentenceModel
# model = SentenceModel('shibing624/text2vec-base-chinese-paraphrase',device="cpu")
# para2vec_model=model
# 需要对数据进行一下预处理，把数据转换成向量。
import sys 
sys.path.append(os.path.dirname( os.path.dirname( os.path.abspath(__file__))))
from merge_vec import get_text_vec
from tqdm import tqdm
def data_load(data_dir):
    """
    加载数据，并且需要把文本数据向量化 
    """
    # 数据格式，0位 text_level, 1 原文，2位置 原文对象的向量。
    data_info={"x":[],"y":[],"text":[],"company_code":[],"embeddings":[]}
    for file in tqdm(os.listdir(data_dir)):
        with open(f"{data_dir}/{file}","r") as txtf:
            company_code=file[:-4]
            #data_info[file[:-4]]={}
            x_list=[]
            y_list=[]
            text_list=[]
            for line in txtf.readlines():
                data=line.split("<->")
                text_level,text=data[0],data[1]
                clear_text=text.removeprefix("\t").removesuffix("\n")
                l=0
                if text_level.strip().isdigit():
                    if int(text_level)>=1 and int(text_level)<=3:
                        l=int(text_level)
                    #data_info[file[:-4]].append([int(text_level),clear_text])
                y_list.append(l)
                #x_list.append(clear_text)
                text_list.append(clear_text)
        #data_info['x'].append(x_list)
        data_info['y'].append(y_list)
        data_info['text'].append(text_list)
        data_info["x"].append([ get_text_vec(text,company_code,index) for index,text in enumerate(text_list)]) # 转换成二维向量
        data_info['company_code'].append(company_code)
    return data_info# 
class TocDataset(Dataset):
    """
    输入是一个文件夹
    中间处理过程：将文件读取出来，然后将数据转化为句向量
    最终处理：是否要
    """
    def __init__(self, data_loder,data_dir):
        self.data_dir = data_dir
        self.data=data_loder(self.data_dir)


    def __len__(self):
        return len(self.data["company_code"])

    def get_info(self, idx):
        loader, rela_idx = self._match_loader(idx)
        return loader.get_data(rela_idx)
        
    def __getitem__(self, idx):
        try:
            # idx = 1
            return [torch.tensor(self.data["x"][idx],dtype=torch.float),torch.tensor(self.data["y"][idx],dtype=torch.long)]
        except Exception as e:
            print('Error occured while load data: %d' % idx)
            raise e
import torch.nn.functional as F
def collate_func(batch_data):
    batch_size = len(batch_data)
    seq_length=[0]*batch_size
    max_seq_length=-1
    for i in range(batch_size):
        seq_length[i]=batch_data[i][0].size(0)
    max_seq_length=max(seq_length)
    mask_attention=torch.ones(batch_size,max_seq_length)
     #[data[0] for data in  batch_data])
    
    for i in range(batch_size):
        batch_data[i][0]=F.pad(batch_data[i][0],(0,0,0,max_seq_length-seq_length[i]))
        batch_data[i][1]=F.pad(batch_data[i][1],(0,max_seq_length-seq_length[i]))
        mask_attention[i][seq_length[i]:]=0
    x_list_tensors=torch.cat([data[0].unsqueeze(0) for data in  batch_data], dim=0)
    y_list_tensors=torch.cat([data[1].unsqueeze(0) for data in  batch_data], dim=0)
    return x_list_tensors,y_list_tensors,mask_attention

toc_ds=TocDataset(data_loder=data_load,data_dir="/home/liukun/multimodal/document_struct/toc/checked")
if __name__=="__main__":
    #data_load("/home/liukun/multimodal/document_struct/toc/checked")
    toc_ds=TocDataset(data_loder=data_load,data_dir="/home/liukun/multimodal/document_struct/toc/checked")
    
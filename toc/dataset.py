from torch.utils.data import Dataset
import os 

# 需要对数据进行一下预处理，把数据转换成向量。
def data_load(data_dir):
    """
    加载数据，并且需要把文本数据向量化 
    """
    # 数据格式，0位 text_level, 1 原文，2位置 原文对象的向量。
    data_info={"x":[],"y":[],"text":[],"company_code":[]}
    for file in os.listdir(data_dir):
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
                    l=int(text_level)
                    #data_info[file[:-4]].append([int(text_level),clear_text])
                y_list.append(l)
                x_list.append(clear_text)
                text_list.append(clear_text)
        data_info['x'].append(x_list)
        data_info['y'].append(y_list)
        data_info['text'].append(text_list)
        data_info['company_code'].append(company_code)
    return data_info# 



    pass 
class TocDataset(Dataset):
    """
    输入是一个文件夹
    中间处理过程：将文件读取出来，然后将数据转化为句向量
    最终处理：是否要
    """
    def __init__(self, data_loder,data_dir,sentence2vec_model):
        self.sentence2vec_model=sentence2vec_model
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
            return dict(
                idx=idx,
                emb=self.data[idx][2],
                text=self.data["text"][idx]
            )
            loader, rela_idx = self._match_loader(idx)
            word = loader.get_data(rela_idx)
            encoder_input, ly, re, align, transcripts, bboxes, stride = self.cal_items(word)
            return dict(
                idx=idx,
                ly=ly,
                re=re,
                align=align,
                bboxes=bboxes,
                transcripts=transcripts,
                encoder_input=encoder_input,
                stride=stride
            )
        except Exception as e:
            print('Error occured while load data: %d' % idx)
            raise e
        
if __name__=="__main__":
    data_load("/home/liukun/multimodal/document_struct/toc/checked")
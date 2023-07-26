"""
使用pymuf解析pdf文件，获取pdf文件的文本和坐标信息
"""

from config import MEDIA_ROOT,PROJECT_ROOT
import os 
import fitz 
from PIL import Image
import json
from math import ceil
from tqdm import tqdm
MUPDF_ROOT=f"{PROJECT_ROOT}/data/mupdf"

def convert_pdf_json():
    for pdf in tqdm(os.listdir(f"{MEDIA_ROOT}/ndbg_zy")):
        try:
            doc=fitz.Document(f"{MEDIA_ROOT}/ndbg_zy/{pdf}")
        except Exception as e:
            print(e)

        doc_data={}
        company_code=pdf[:6]
        for page in doc.pages():
            doc_data[int(page.number)]={}
            doc_data[int(page.number)]['words_list']=[]
            for words in page.get_text("words"):
                bl=1654/page.rect.width
                x0=int(words[0]*bl)
                y0=int(words[1]*bl) 
                x1=ceil(words[2]*bl)
                y1=ceil(words[3]*bl)
                doc_data[page.number]['words_list'].append(
                    [
                    x0,y0,x1,y1,words[4] 
                    ]
                )
                # img=Image.open("data/image/000001/0000010001-01.png")
                # img.crop([x0,y0,x1,y1]).show()
                # print(words[4])
        with open(f"{MUPDF_ROOT}/{company_code}.json",'w') as jf:
            json.dump(doc_data,jf,ensure_ascii=False,indent=2)
        #print(doc_data)
                        

if __name__=="__main__":
    convert_pdf_json()
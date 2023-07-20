# 裁剪表格中的图片
from utils import get_image_list,smart_mkdirs
from tqdm import tqdm
import os
import json
import re
from config import DOC_ROOT_PATH,MEDIA_ROOT
def load_json_data(basic_dir):
    """
    硬代码，文件夹中，pdf按照页分析，重新组织起来。
    """
    info_dict={}
    for xdir in tqdm(os.listdir(basic_dir)):
        try:
            info_dict[xdir]=json.load(open(f"{basic_dir}/{xdir}/doc.json","r"))
        except Exception as e:
            print(e)
            #print(xdir,page_no,json_data)
    #print(info_dict)
    return info_dict

        
                               
                               
def crop_table(company_code):
    pass 
def crop_table_image():
    doc_info=load_json_data(DOC_ROOT_PATH)
    for company_code,doc_data in tqdm(doc_info.items()):
        smart_mkdirs(f"{MEDIA_ROOT}/crop_table/{company_code}",rm=True)
        image_info=get_image_list(company_code)
        for page_id,page_data in doc_data["page_info"].items():
            print(page_id)
            table_id=0
            for content in page_data["content"]:
                if content["type"]=="table":
                    index=content["block_index"]

                    #print(page_data["layout"][index])
                    
                    x,y,width,height=page_data["layout"][index][0],page_data["layout"][index][1],page_data["layout"][index][3],page_data["layout"][index][4]
                    img=image_info[int(page_id)]['img']
                    crop_img=img.crop([x,y,x+width,y+height])
                    crop_img.save(f"{MEDIA_ROOT}/crop_table/{company_code}/page_{int(page_id):02d}_table_{table_id:02d}.png",format='png')
                    table_id+=1




if __name__=="__main__":
    # data=load_json_data(DOC_ROOT_PATH)
    # print(len(data))
    crop_table_image()
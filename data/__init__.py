import json
from tqdm import tqdm
import os
import re
from PIL import Image
def dump_json_data(data,data_path):
    with open(data_path,'w') as f:
        json.dump(data,f,ensure_ascii=False,indent=2)
    pass 
def load_json_data(basic_dir):
    """
    硬代码，文件夹中，pdf按照页分析，重新组织起来。
    """
    info_dict={}
    for xdir in tqdm(os.listdir(basic_dir)):
        info_dict[xdir]={}
        for f_json_name in  os.listdir(f"{basic_dir}/{xdir}"):

            re_result=re.search("\d+-(?P<page_no>\d+).json",f_json_name)
            if re_result:
                try:
                    page_no=int(re_result.groupdict()['page_no'])
                    json_data=json.load(open(f"{basic_dir}/{xdir}/{f_json_name}","r"))
                    info_dict[xdir][page_no]=json_data
                except Exception as e:
                    print(e)
                    del info_dict[xdir]
                    break
                #print(xdir,page_no,json_data)
    #print(info_dict)
    return info_dict

def load_image_data(basic_dir):
    """
    硬代码，文件夹中，pdf按照页分析，重新组织起来。
    """
    info_dict={}
    for xdir in tqdm(os.listdir(basic_dir)):
        info_dict[xdir]={}
        for f_png_name in  os.listdir(f"{basic_dir}/{xdir}"):
            re_result=re.search("\d+-(?P<page_no>\d+).png",f_png_name)
            if re_result:
                page_no=int(re_result.groupdict()['page_no'])
                img=Image.open(f"{basic_dir}/{xdir}/{f_png_name}")
                json_data={"width":img.width,"height":img.height}
                info_dict[xdir][page_no]=json_data
                #print(xdir,page_no,json_data)
    #print(info_dict)
    return info_dict


import shutil
def smart_mkdirs(dir_path,rm=False):
    if not os.path.exists(dir_path):
        os.makedirs(dir_path)
    elif rm:
        shutil.rmtree(dir_path)
        os.makedirs(dir_path)
    
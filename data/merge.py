# 合并所有的Python文件
import os
import json  
import re 
PROJECT_ROOT=os.path.dirname(
    os.path.dirname(
    os.path.abspath(__file__)))
# infer_dir_list=os.listdir("infer")
infer_dict={}
def dump_json_data(data,data_path):
    with open(data_path,'w') as f:
        json.dump(data,f,ensure_ascii=False)
    pass 
def load_json_data(basic_dir):
    """
    硬代码，文件夹中，pdf按照页分析，重新组织起来。
    """
    info_dict={}
    for xdir in os.listdir(basic_dir):
        info_dict[xdir]={}
        for f_json_name in  os.listdir(f"{basic_dir}/{xdir}"):
            re_result=re.search("\d+-(?P<page_no>\d+).json",f_json_name)
            if re_result:
                page_no=int(re_result.groupdict()['page_no'])
                json_data=json.load(open(f"{basic_dir}/{xdir}/{f_json_name}","r"))
                info_dict[xdir][page_no]=json_data
                #print(xdir,page_no,json_data)
    print(info_dict)
    return info_dict
# ocr_dir_list=os.listdir("ocr")
import shutil
def smart_mkdirs(dir_path,rm=False):
    if not os.path.exists(dir_path):
        os.makedirs(dir_path)
    elif rm:
        shutil.rmtree(dir_path)
        os.makedirs(dir_path)
    

def merge_data():
    """
    按照pdf文档，把所有的识别数据和ocr数据组合起来。
    """
    infer_data=load_json_data(f"{PROJECT_ROOT}/data/infer")
    ocr_data=load_json_data(f"{PROJECT_ROOT}/data/ocr")
    os.makedirs(f"{PROJECT_ROOT}/data/core",exist_ok=True)
    merge_root_path=f"{PROJECT_ROOT}/data/core"
    for company_code in infer_data.keys()&ocr_data.keys():
        smart_mkdirs(f"{merge_root_path}/{company_code}")
        for page_id in range(1,len(infer_data[company_code])+1):
            page_infer_data=infer_data[company_code][page_id]
            page_ocr_data=ocr_data[company_code][page_id]
            for node in page_ocr_data[0]:
                #print(node)
                pass
            print(company_code,page_id,len(page_ocr_data[0])) 
            # for page_node,node_data in ocr_data[company_code].items():
            # dump_json_data(node_data,f"{merge_root_path}/{company_code}/infer-{page_node}.json")
        
            # dump_json_data(node_data,f"{merge_root_path}/{company_code}/ocr-{page_node}.json")

def process_doc_file(doc_dir_path):
    pass 
    


    # print(company_code_list)
if __name__=="__main__":
    merge_data()
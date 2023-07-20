# 合并所有的Python文件
import os
import json  
import re 
from PIL import Image 
from collections import defaultdict
import copy
from tqdm import tqdm
PROJECT_ROOT=os.path.dirname(
    os.path.dirname(
    os.path.abspath(__file__)))
from data import load_json_data,dump_json_data,load_image_data,smart_mkdirs
from merge import MEDIA_ROOT
def text_json_data(data,data_path):
    """
    把解析出来的docjson的数据以txt的形式展现出来
    """
    txtfile=open(data_path,"w")
    page_info = data["page_info"]
    for page_num in range(1,data["meta_info"]["page_count"]+1):
        content_list = page_info[page_num]["content"]
        for content in content_list:
            if content["type"]=="metainfo":
                txtfile.write("\t".join(content["content"]))
            elif content["type"]=="Text":
                txtfile.write(" "*4)
                txtfile.write("".join(content["content"]))
            elif content["type"]=="Title":
                txtfile.write("".join(content["content"]))
            elif content["type"]=="Section-header":
                txtfile.write("".join(content["content"]))
            elif content["type"]=="table":
                txtfile.write(f"<table id=table_id page_num={page_num}>\n")
            elif content["type"]=="Picture":
                txtfile.write(f"<Picture id=Picture_id page_num={page_num}>\n")
            elif content["type"]=="note":
                txtfile.write("\t"*4)
                txtfile.write("".join(content["content"]))
            elif content["type"]=="unknow":
                content="".join(content["content"])
                if len(content)>5:
                    txtfile.write(content)
            else:
                print("".join(content["content"]))

            txtfile.write("\n")








def bb_intersection_over_union(boxA, boxB):
    boxA = [int(x) for x in boxA]
    boxB = [int(x) for x in boxB]

    xA = max(boxA[0], boxB[0])
    yA = max(boxA[1], boxB[1])
    xB = min(boxA[2], boxB[2])
    yB = min(boxA[3], boxB[3])

    interArea = max(0, xB - xA + 1) * max(0, yB - yA + 1)

    boxAArea = (boxA[2] - boxA[0] + 1) * (boxA[3] - boxA[1] + 1)
    boxBArea = (boxB[2] - boxB[0] + 1) * (boxB[3] - boxB[1] + 1)
    
    iou = interArea / float(boxAArea + boxBArea - interArea)
    return iou
def get_intersection(boxA, boxB):
    boxA = [int(x) for x in boxA]
    boxB = [int(x) for x in boxB]

    xA = max(boxA[0], boxB[0])
    yA = max(boxA[1], boxB[1])
    xB = min(boxA[2], boxB[2])
    yB = min(boxA[3], boxB[3])

    interArea = max(0, xB - xA + 1) * max(0, yB - yA + 1)

    boxAArea = (boxA[2] - boxA[0] + 1) * (boxA[3] - boxA[1] + 1)
    boxBArea = (boxB[2] - boxB[0] + 1) * (boxB[3] - boxB[1] + 1)
    
    
    return interArea

def old_merge_data():
    """
    按照pdf文档，把所有的识别数据和ocr数据组合起来。
    """
    infer_data=load_json_data(f"{PROJECT_ROOT}/data/infer")
    ocr_data=load_json_data(f"{PROJECT_ROOT}/data/ocr")
    image_data=load_image_data(f"{PROJECT_ROOT}/data/image")
    os.makedirs(f"{PROJECT_ROOT}/data/core",exist_ok=True)
    merge_root_path=f"{PROJECT_ROOT}/data/core"
    for company_code in infer_data.keys()&ocr_data.keys():
        smart_mkdirs(f"{merge_root_path}/{company_code}")
        
        for page_id in range(1,len(infer_data[company_code])+1):
            page_infer_data=infer_data[company_code][page_id]
            page_ocr_data=ocr_data[company_code][page_id]
            page_image_data=image_data[company_code][page_id]
            page_width,page_height=page_image_data['width'],page_image_data['height']
            layout_black_list=[]
            crash=False
            for node in page_infer_data[0]["result"]:#[0]["value"]:
                # print(node["value"]["rectanglelabels"][0])
                # print(node["value"]["x"]*page_width*0.01,
                #       node["value"]["y"]*page_height*0.01,
                #       node["value"]["width"]*page_width*0.01,
                #       node["value"]["height"]*page_height*0.01
                #       )
                layout_black_list.append([
                    node["value"]["x"]*page_width*0.01,
                    node["value"]["y"]*page_height*0.01,
                    -node["value"]["width"]*node["value"]["height"],# 排序使用
                    node["value"]["width"]*page_width*0.01,
                    node["value"]["height"]*page_height*0.01,
                    node["score"],
                    node["value"]["rectanglelabels"][0]
                    ]
                )
                # 
            
            layout_black_list.sort(key= lambda x: (x[5],-x[2]),reverse=True)#优先级越高，越靠前。
            i=0
            blocks_len=len(layout_black_list)
            graph=[[0]*(blocks_len+1) for _ in range(blocks_len+1)]
            max_position=[i for  i in range(blocks_len+1)]
            while i <blocks_len-1:
                next_i=i+1
                j=i+1
                while j<blocks_len:
                    iou=bb_intersection_over_union(
                        [
                        layout_black_list[i][0] 
                        ,layout_black_list[i][1]
                        ,layout_black_list[i][0] +layout_black_list[i][3],
                        layout_black_list[i][1]+layout_black_list[i][4]
                        ],
                        [
                        layout_black_list[j][0] 
                        ,layout_black_list[j][1]
                        ,layout_black_list[j][0]+layout_black_list[j][3],
                        layout_black_list[j][1]+layout_black_list[j][4]
                        ]
                    )
                    if iou>0:
                        crash=True
                        graph[i][j]=1
                        max_position[i]=j
                        # graph[i].append([
                        #     j,
                        #     iou,
                        #     -layout_black_list[j][2],# 区域的面积，
                        #     layout_black_list[j][5],# 置信度
                        #     layout_black_list[j][6],# 类别
                        # ])
                    else:
                        break
                    j=j+1
                # if i in graph:
                #     graph[i].append(j)
                    # graph[i].insert(
                    #     0,
                    #     [
                    #         i,
                    #         1,
                    #         -layout_black_list[i][2],# 区域的面积，
                    #         layout_black_list[i][5],# 置信度
                    #         layout_black_list[i][6],# 类别
                    #     ]
                    # )
                i+=1


            # for i in range(len(layout_black_list)-2):
            #     iou=bb_intersection_over_union(
            #         [
            #         layout_black_list[i][0] 
            #          ,layout_black_list[i][1]
            #          ,layout_black_list[i][0] +layout_black_list[i][3],
            #          layout_black_list[i][1]+layout_black_list[i][4]
            #          ],
            #          [
            #         layout_black_list[i+1][0] 
            #          ,layout_black_list[i+1][1]
            #          ,layout_black_list[i+1][0]+layout_black_list[i+1][3],
            #          layout_black_list[i+1][1]+layout_black_list[i+1][4]
            #          ]
            #     )
            #     if iou>0:
            #         print(iou,
            #             [i,layout_black_list[i][-1],layout_black_list[i][-2]],
            #             [i+1,layout_black_list[i+1][-1],layout_black_list[i+1][-2]])
            #         graph[i]=i+1
                
            if crash:
                #print(graph)
                print(max_position)
                i=1
                while i < len(max_position):# range(1,len(max_position)):
                    if i == max_position[i]:
                        i=i+1
                        continue
                    next_border=max_position[i]
                    j=i+1
                    while j<=next_border and j< len(max_position):
                        next_border=max(max_position[j],next_border)
                        max_position[i]=next_border
                        max_position[j]=-max_position[j]# 做个标记，表示已经处理过了。
                        j=j+1
                    i=j 
                print(max_position)# 分治成了子图的模式。
                # 一种模式，群里面的图都是某个图的子图。
                # 看一下子图是不是两个的情况。
                # 找到子图
                i=1
                while i < len(max_position):
                    if max_position[i]<0 or max_position[i]==i:
                        i=i+1
                        continue
                    if max_position[i]-i==1:
                        # 一种是相交
                        # 一种是一个是另一个的子图
                        # 如果iou<10，那就是相交了很少一部分。
                        pass 
                    i=i+1
            # 一种是包含的情况。
            # 一种是相交的情况。 如果相交小的情况下，
            # 一种是等于的情况。

                            
            #print(company_code,page_id,len(page_ocr_data[0])) 
            # for page_node,node_data in ocr_data[company_code].items():
            # dump_json_data(node_data,f"{merge_root_path}/{company_code}/infer-{page_node}.json")
            # dump_json_data(node_data,f"{merge_root_path}/{company_code}/ocr-{page_node}.json")
            ocr_mapping=defaultdict(list)
            ocr_block_stack=[]
            for node_index , node in enumerate(page_ocr_data[0]):
                #print(node)
                x0,y0=min([x[0] for x in node[0]]),min([x[1] for x in node[0]])
                x1,y1=max([x[0] for x in node[0]]),max([x[1] for x in node[0]])
                ocr_area=(y1+1-y0)*(x1+1-x0)
                #print([x0,y0,x1,y1] ,node[1][0])
                for block_index,block in enumerate(layout_black_list):
                    bx0,by0=block[0],block[1]
                    bx1,by1=block[3]+block[0],block[4]+block[1]
                    is_area=get_intersection(
                        [x0,y0,x1,y1]
                        ,
                        [bx0,by0,bx1,by1]
                        )
                    if is_area/ocr_area>0.85:
                        ocr_mapping[node_index].append(
                            [block[-1],block[-2],block_index,node[1][0]]
                        )
                        if ocr_block_stack and ocr_block_stack[-1]["block_index"]==block_index:
                            ocr_block_stack[-1]["content"].append(node[1][0])
                        else:
                            ocr_block_stack.append(
                                {
                                    "block_index":block_index,
                                    "content":[node[1][0]],
                                    "type":block[-1]
                                }
                            )
                        break
                if len(ocr_mapping[node_index])==0:
                    ocr_block_stack.append(
                                {
                                    "block_index":-1,
                                    "content":[node[1][0]],
                                    "type":"unknow"
                                }
                            )
            # 先想办法输出一个block的情况。
        
def merge_data():
    """
    按照pdf文档，把所有的识别数据和ocr数据组合起来。
    """
    # infer_data=load_json_data(f"{PROJECT_ROOT}/data/infer")
    # ocr_data=load_json_data(f"{PROJECT_ROOT}/data/ocr")
    # image_data=load_image_data(f"{PROJECT_ROOT}/data/image")
    # merge_root_path=f"{PROJECT_ROOT}/data/core"
    os.makedirs(f"{PROJECT_ROOT}/data/core",exist_ok=True)
    merge_root_path=f"{PROJECT_ROOT}/data/core"
    infer_data=load_json_data(f"{MEDIA_ROOT}/ndbg_zy_infer")
    ocr_data=load_json_data(f"{MEDIA_ROOT}/ndbg_zy_ocrs")
    image_data=load_image_data(f"{MEDIA_ROOT}/ndbg_zy_images")

    for company_code in tqdm(infer_data.keys()&ocr_data.keys(),desc="推理和ocr生成文本内容"):
        smart_mkdirs(f"{merge_root_path}/{company_code}")
        try:
            doc_json=merge_one_doc(company_code,infer_data,ocr_data,image_data)
            dump_json_data(doc_json,f"{merge_root_path}/{company_code}/doc.json")
            text_json_data(doc_json,f"{merge_root_path}/{company_code}/doc.txt")#
        except Exception as e:
            print(company_code,e)


def merge_one_doc(company_code,infer_data,ocr_data,image_data):

    doc_file_info={}
    doc_data={
        "meta_info":{
        "company_code":company_code,
        "page_count":len(infer_data[company_code]),
        },
        "page_info":doc_file_info
        }
    for page_id in range(1,len(infer_data[company_code])+1):
        doc_file_info[page_id]={}
        page_infer_data=infer_data[company_code][page_id]
        page_ocr_data=ocr_data[company_code][page_id]
        page_image_data=image_data[company_code][page_id]
        page_width,page_height=page_image_data['width'],page_image_data['height']
        layout_black_list=[]
        for node in page_infer_data[0]["result"]:#[0]["value"]:
            layout_black_list.append([
                node["value"]["x"]*page_width*0.01,
                node["value"]["y"]*page_height*0.01,
                -node["value"]["width"]*node["value"]["height"],# 排序使用
                node["value"]["width"]*page_width*0.01,
                node["value"]["height"]*page_height*0.01,
                node["score"],
                node["value"]["rectanglelabels"][0]
                ]
            )
        
        layout_black_list.sort(key= lambda x: (x[5],-x[2]),reverse=True)#准确率越高，面积越大，越靠前
        doc_file_info[page_id]["layout"]=layout_black_list # 记录layout的信息
        ocr_mapping=defaultdict(list)
        ocr_block_stack=[]
        for node_index , node in enumerate(page_ocr_data[0]):
            x0,y0=min([x[0] for x in node[0]]),min([x[1] for x in node[0]])
            x1,y1=max([x[0] for x in node[0]]),max([x[1] for x in node[0]])
            ocr_area=(y1+1-y0)*(x1+1-x0)
            for block_index,block in enumerate(layout_black_list):
                bx0,by0=block[0],block[1]
                bx1,by1=block[3]+block[0],block[4]+block[1]
                is_area=get_intersection(
                    [x0,y0,x1,y1]
                    ,
                    [bx0,by0,bx1,by1]
                    )
                if is_area/ocr_area>0.85:
                    ocr_mapping[node_index].append(
                        [block[-1],block[-2],block_index,node[1][0]]
                    )
                    if ocr_block_stack and ocr_block_stack[-1]["block_index"]==block_index:
                        ocr_block_stack[-1]["content"].append(node[1][0])
                        ocr_block_stack[-1]["location"].append(node[0])
                    else:
                        ocr_block_stack.append(
                            {
                                "block_index":block_index,
                                "content":[node[1][0]],
                                "location":[node[0]],
                                "type":block[-1]
                            }
                        )
                    break# 确保每一个区域都可以被打上一个标签。
            if len(ocr_mapping[node_index])==0:
                ocr_block_stack.append(
                            {
                                "block_index":-1,
                                "content":[node[1][0]],
                                "location":[node[0]],
                                "type":"unknow"
                            }
                        )
        doc_file_info[page_id]["content"]=ocr_block_stack
    #print(json.dumps(doc_file_info,ensure_ascii=False,indent=2))
    return doc_data   
    



    # print(company_code_list)
if __name__=="__main__":
    merge_data()
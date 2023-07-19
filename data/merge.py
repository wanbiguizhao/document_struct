# 合并所有的Python文件
import os
import json  
import re 
from PIL import Image 
from collections import defaultdict
import copy
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
    #print(info_dict)
    return info_dict
def load_image_data(basic_dir):
    """
    硬代码，文件夹中，pdf按照页分析，重新组织起来。
    """
    info_dict={}
    for xdir in os.listdir(basic_dir):
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
# ocr_dir_list=os.listdir("ocr")
import shutil
def smart_mkdirs(dir_path,rm=False):
    if not os.path.exists(dir_path):
        os.makedirs(dir_path)
    elif rm:
        shutil.rmtree(dir_path)
        os.makedirs(dir_path)
    
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
def get_sub_graph(graph):
    pass 
    # 某个节点是可取消的。
    # 某个节点的区域要发生变化。
    # 之后重新再跑一下图
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
                    else:
                        break
                    j=j+1
                i+=1
                
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
            ocr_mapping=defaultdict(list)
            ocr_block_stack=[]
            for node_index , node in enumerate(page_ocr_data[0]):
                #print(node)
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
            
            print(json.dumps(ocr_block_stack,ensure_ascii=False,indent=2))
            print("")

def process_doc_file(doc_dir_path):
    pass 
    


    # print(company_code_list)
if __name__=="__main__":
    merge_data()
# 一些正则式，用于区分不同层级的标题

import re
from typing import Any 
from config import APP_ROOT
class Rule:
    def __init__(self,rid,rule_regex) -> None:
        self.rid=rid
        self.regex=re.compile(rule_regex)
    def __call__(self, text) -> Any:
        match=self.regex.match(text)
        if match:
            return True
        return False


def infer_toc(doc_text_list,doc_name):
    # 输入是文本，输出是文字大纲级别的预测
    rule_list:list[Rule]=[
    Rule(1,"第[一二三四五六七八九十]节"),
    Rule(11,"^\s*?[一二三四五六七八九十]、"),
    Rule(2,"^[ ]*?\d+?[^\.、]"),
    Rule(3,"[ ]*\d+、"),
    Rule(4,"[ ]*\d+(．|\.)[^\d]"),
    Rule(5,"\d\d?\.\d[ ]?"),
    Rule(6,"[(（][一二三四五六七八九十]+[）)]"),
    Rule(7,"[(（][1234567890]+[）)]"),
    Rule(8,"\s+[1234567890]+[）)]\s{0,2}"),
    Rule(9,"^\s*[①②③]+"),
    Rule(10,"\d+\.\d+\.\d[^\s]"),
    Rule(11,"^[ ]*\d+\.\d+\.\d\.\d[^\d\.]"),
    Rule(12,"^[ ]*\d+\.\d+\.\d\.\d\.\d[^\d]"),
    ]
    toc_level_mapping={}# rid:level
    doc_level_mapping={}
    current_level=-1
    level_stack=[]
    for index,text in enumerate(doc_text_list):
        if "重要提示" in text:
            doc_level_mapping[index]=1
            

        text_level=0
        hit_flag=False
        for rule in rule_list:
            #"".lstrip()
            # if re.match("(\d+年)|(%)",text):
            #     continue
            if rule(text.lstrip()):
                if re.search("^\d\d\d\d年|^\d+%|\d+尺|\d+MWh",text.lstrip()):# "月" in text.lstrip() or "%" in text  :
                    continue
                
                if hit_flag and len(text)<20:
                    print("ERROR：",text,rule.regex.pattern)
                hit_flag=True
                if len(level_stack)==0:
                    level_stack.append(rule.rid)
                    toc_level_mapping[rule.rid]=rule
                    text_level=1
                else:
                    if rule.rid in toc_level_mapping:
                        while rule.rid!=level_stack[-1]:
                            rid=level_stack.pop(-1)
                            del toc_level_mapping[rid]
                            
                    else:
                        level_stack.append(rule.rid)
                        toc_level_mapping[rule.rid]=rule
                text_level=len(level_stack)
                # if text_level>0:
                #     print(text_level,text,toc_level_mapping[level_stack[-1]].regex.pattern)
        #text_level=len(level_stack)
        if index not in doc_text_list:
            doc_level_mapping[index]=text_level
        #print(text_level,text[:15])

    with open(f"{APP_ROOT}/tmp/{doc_name}.txt","w") as wf:
        for index,text_level in doc_level_mapping.items():
            if len(doc_text_list[index].replace("\n","").strip())==0:
                continue
            tab=0
            if text_level==0:
                tab=5
            else:
                tab=min(5,text_level)
            wf.write(f"{text_level}{'  '*tab}<->\t{doc_text_list[index].strip()}\n")
            #print(text_level,"<->",doc_text_list[index].lstrip())        
    doc_text_list

def pipline01():
    from data.utils import load_doc_text_data
    from data.config import DOC_ROOT_PATH
    doc_info=load_doc_text_data(DOC_ROOT_PATH)
    for doc_name ,doc_text_list in doc_info.items():
        print("="*10)
        infer_toc(doc_text_list,doc_name)
if __name__=="__main__":
    pipline01()
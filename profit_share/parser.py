import re
import inspect
import json
import os 
class ProfitSharingPlan:
    """
    利润分配方案
    """
    def __init__(self) -> None:
        self.idset=set()
        self.entities_list=[]
        self.ie_func_list=[f[1] for f in inspect.getmembers(self,predicate=inspect.ismethod) if f[0].startswith("ie_")] # 把所有的提取函数都集中起来运行
    def set_input(self,input_text):
        self.text=input_text
        self.entities_list=[]

    def ie_bonus_share(self):
        """
        红利派发
        """
        pattern=re.compile("(?P<fen>每\d+股).*现金.*(?P<je>\d+元)")
        match=pattern.search(self.text)
        if match:
            regs=match.regs
            self.entities_list.append({
                "id":1,"label":"红利基数","start_offset":regs[1][0],"end_offset":regs[1][1],"value":match.group(1)
            })
            self.entities_list.append({
                "id":1,"label":"红利金额","start_offset":regs[2][0],"end_offset":regs[2][1],"value":match.group(2)
            })
    def ie_bonus_issue(self):
        """
        红股派发 
        """
        pattern=re.compile(".*(?P<zgj>每\d+股).*送红股(?P<zg>\d+股)")
        match=pattern.search(self.text)
        if match:
            regs=match.regs
            self.entities_list.append({
                "id":1,"label":"红股基数","start_offset":regs[1][0],"end_offset":regs[1][1],"value":match.group(1)
            })
            self.entities_list.append({
                "id":1,"label":"红股股数","start_offset":regs[2][0],"end_offset":regs[2][1],"value":match.group(2)
            })
    def ie_capitalization_of_capital_reserves(self):
        """
        资本公积金转增股
        """
        print(inspect.stack()[0][3][3:])
        pattern=re.compile("资本.*(?P<zgj>每\d+股).*转增.*(?P<zg>\d+股)")
        match=pattern.search(self.text)
        if match:
            regs=match.regs
            self.entities_list.append({
                "id":1,"label":"转增基数","start_offset":regs[1][0],"end_offset":regs[1][1],"value":match.group(1)
            })
            self.entities_list.append({
                "id":1,"label":"转增股数","start_offset":regs[2][0],"end_offset":regs[2][1],"value":match.group(2)
            })
    def ie_cardinal_number(self):
        """
        利润分配的基数
        """
        pattern=re.compile("以.*?([\d,]+[股]?)为基数")
        match=pattern.search(self.text)
        if match:
            regs=match.regs
            self.entities_list.append({
                "id":1,"label":"总基数","start_offset":regs[1][0],"end_offset":regs[1][1],"value":match.group(1)
            })
    def run(self):
        for ie_f in self.ie_func_list:
            ie_f(),
    def get_output(self,id):
        return {"id":id,"entities":self.entities_list,'text':self.text,"relations":[],"Comments":[]}

def convert_pipline01():
    current_path=os.path.dirname(os.path.abspath(__file__))
    psp=ProfitSharingPlan()
    with open(f"{current_path}/lifen.txt",'r') as rf,open(f"{current_path}/lifen.jsonl",'w')as  wf:
        i=1
        for line in rf.readlines():
            psp.set_input(line.replace("\n",""))
            psp.run()
            wf.write(json.dumps(psp.get_output(id=i),ensure_ascii=False)+"\n")
            i+=1

if __name__=="__main__":
    # psp=ProfitSharingPlan()
    # psp.set_input("公司经本次董事会审议通过的利润分配预案为：以152,537,820为基数，向全体股东每10股派发现金红利20元（含税），送红股0股（含税），以资本公积金向全体股东每10股转增5股。")
    # psp.run()
    # print(psp.entities_list)
    # psp.set_input("公司经本次董事会审议通过的利润分配预案为：以152,537,820为基数，向全体股东每10股派发现金红利20元（含税），每15股送红股0股（含税），以资本公积金向全体股东每10股转增5股。")
    # psp.run()
    # print(json.dumps(psp.get_output(),ensure_ascii=False))
    convert_pipline01()
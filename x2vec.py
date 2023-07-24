# 把doc中的内容变成vec方便快速搜索。
import chromadb
from tqdm import tqdm
# setup Chroma in-memory, for easy prototyping. Can add persistence easily!
client = chromadb.PersistentClient("vecdb.db/vecdb.db")
# Create collection. get_collection, get_or_create_collection, delete_collection also available!
# collection = client.create_collection("ndbg_zy_2022")

# # Add docs to the collection. Can also update and delete. Row-based API coming soon!
# collection.add(
#     documents=["This is document1", "This is document2"], # we handle tokenization, embedding, and indexing automatically. You can skip that and add your own embeddings as well
#     metadatas=[{"source": "notion"}, {"source": "google-docs"}], # filter on these!
#     ids=["doc1", "doc2"], # unique for each doc
# )

# # Query/search 2 most similar results. You can also .get by id
# results = collection.query(
#     query_texts=["This is a query document"],
#     n_results=2,
#     # where={"metadata_field": "is_equal_to_this"}, # optional filter
#     # where_document={"$contains":"search_string"}  # optional filter
# )
from data.utils import load_doc_text_data
from embedding import para2vec_model
from data.config import DOC_ROOT_PATH

def doc2vec_db():
    collection = client.create_collection("ndbg_zy_2022")
    doc_code_dict=load_doc_text_data(DOC_ROOT_PATH)
    i=0
    for company_code,text_list in tqdm(doc_code_dict.items()):
        for ti,text in enumerate(text_list):
            collection.add(
                embeddings=para2vec_model.encode(text).tolist(),
                documents=text, # we handle tokenization, embedding, and indexing automatically. You can skip that and add your own embeddings as well
                metadatas={"source": "dbzy"}, # filter on these!
                ids=f"{company_code}-{ti:3d}", # unique for each doc
            )
            #print(ti)
        i+=1
        if i==200:
            break
    query_vec=para2vec_model.encode("公司经本次董事会审议通过的利润分配预案为：以506,521,849为基数，向全体股东每10股派发现金红利0.60元（含税），送红股0股（含税），不以公积金转增股本。").tolist()
    result=collection.query(query_vec)
    print(result)
    return collection
def query_db():
    collection = client.get_collection("ndbg_zy_2022")
    doc_code_dict=load_doc_text_data(DOC_ROOT_PATH)
    query_vec=para2vec_model.encode("事务所（特殊普通合伙）为本公司出具了标准无保留意见的审计报告").tolist()
    
    for company_code,text_list in tqdm(doc_code_dict.items()):
        #query_vec=para2vec_model.encode("是一家专业从事某一行业的企业主要行业包括").tolist()
        result=collection.query(query_vec,n_results=1,where={"code": company_code})

        for doc in zip(result["documents"][0],result["distances"][0]):
            if doc[1]<110:
                print(doc) 
        
    #print(result["documents"])

def get_meta_info(company_code,text_list):
    # doc_code_dict=load_doc_text_data(DOC_ROOT_PATH)
    # for company_code,text_list in tqdm(doc_code_dict.items()):
    import re 
    full_company_name=""
    company_name=""
    for text in text_list[:6]:
        match=re.search("^(.*?有限公司)[ 0-9$]?",text.replace("\n","").strip())
        if match and not full_company_name:
            full_company_name=match.group(1)
        if "简称" in text:
            for x in [t for t in text.split("\t") if "简称" in t]:
                company_name=x.split("：")[-1]
        # company_name_match=re.search(r"简称：([^0-9]*?) |简称：([^0-9]*?)\t|简称：([^0-9]*?)$|简称：([^0-9]*?)[0-9]",text.strip(),re.MULTILINE)
        # if company_name_match:
        #     company_name=company_name_match.group(1)
    ans=[]
    if full_company_name:
        ans.append(
           [f"告诉股票代码{company_code}的公司全称?",f"{full_company_name}"]
        )
        ans.append(
           [f"{full_company_name}的股票代码?",f"{company_code}"]
        )
    if company_name:
        ans.append(
           [f"告诉股票代码{company_code}的公司简称?",f"{company_name}"]
        )
        ans.append(
           [f"{company_name}的股票代码?",f"{company_code}"]
        )
    if company_name and full_company_name:
        ans.append(
            [f"公司{company_name}的全称是?",f"{full_company_name}"]
        )
        ans.append(
            [f"{full_company_name}的简称是?",f"{company_name}"]
        )

    print(ans)

    return {"company_code":company_code,"company_name":company_name,"full_company_name":full_company_name,"meta_info":ans} 
def get_(text_list):
    """报告期主要业务或产品简介"""
    beg=False
    ans=[]
    for text in text_list:
        
            
        if "主要会计数据和财务指标" in text:
            break 
        if beg:
            ans.append(text)
        if "报告期主要业务或产品简介" in text:
            beg=True
    return ans

def pipline02():
    """
    批量获取一些结构化信息
    """
    doc_code_dict=load_doc_text_data(DOC_ROOT_PATH)
    for company_code,text_list in tqdm(doc_code_dict.items()):
        sft_info=get_meta_info(company_code,text_list)
        get_(text_list)
        #找到一些公司业务
        print(sft_info)

if __name__=="__main__":
    query_db()
    #pipline02()
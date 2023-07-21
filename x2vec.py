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
    query_vec=para2vec_model.encode("公司经本次董事会审议通过的利润分配预案为：以未来实施分配方案时股权登记日的总股本为基数，向全体股东每10股派发现金红利1元（含税），送红股0股（含税），以资本公积金向全体股东每10股转增0股").tolist()
    result=collection.query(query_vec,n_results=50)
    for doc in result["documents"][0]:
        print(doc) 
    #print(result["documents"])

if __name__=="__main__":
    query_db()
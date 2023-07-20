from text2vec import SentenceModel
sentences = ['如何更换花呗绑定银行卡', '花呗更改绑定银行卡']
model = SentenceModel('shibing624/text2vec-base-chinese-paraphrase',device="cpu")
para2vec_model=model
embeddings = model.encode(sentences)
print(embeddings)
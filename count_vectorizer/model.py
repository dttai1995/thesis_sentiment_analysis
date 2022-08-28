from pandas import ExcelWriter

vectorizer = CountVectorizer()

corpus = [
    'This is the first document.',
    'This is the second second document.',
    'And the third one',
    'Is this the first one?'
]
X = vectorizer.fit_transform(corpus)
analyze = vectorizer.build_analyzer()


bigram_vectorizer = CountVectorizer(ngram_range=(1, 2),)
vectorizer.get_feature_names_out()
X.toarray()
print(vectorizer.vocabulary_.get('document'))



# X = vectorizer.fit_transform(corpus)



import pandas


excel_file = pandas.read_excel("thesis_sentiment_analysis_data.xlsx", index_col=None, header=0)

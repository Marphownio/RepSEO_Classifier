FROM python:3.8

WORKDIR /RepSEO_Classifier

COPY . .

RUN pip3 install -r requirements.txt && \
    python3 download_tranco_list.py && \
    python3 download_nltk_model.py && \
    chmod +x download_word2vec_model.sh && \
    ./download_word2vec_model.sh

ENV WIKI_PATH="/RepSEO_Classifier/wiki.en.vec"
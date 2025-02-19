FROM python:3.8

WORKDIR /RepSEO_Classifier

COPY . .

RUN pip3 install -r requirements.txt && \
    python3 download_tranco_list.py && \
    python3 download_nltk_model.py && \
    wget https://dl.fbaipublicfiles.com/fasttext/vectors-wiki/wiki.en.zip && \
    unzip wiki.en.zip

ENV WIKI_PATH="/RepSEO_Classifier/wiki.en.vec"
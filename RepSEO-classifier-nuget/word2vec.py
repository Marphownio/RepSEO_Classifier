import json
import re
import time
import hashlib
import os
import nltk
import wordninja
import requests
from pygoogletranslation import Translator
from gensim.models.keyedvectors import KeyedVectors
from gensim.parsing.preprocessing import STOPWORDS
from nltk.tokenize import word_tokenize
from db.db_init import get_locale

from langdetect import detect_langs, LangDetectException
from langdetect import DetectorFactory

proxy = {
    "http": "127.0.0.1:4780",
    "https": "127.0.0.1:4780"
}

baidu_appid = os.environ.get('BAIDU_APPID')
if baidu_appid == None:
    baidu_appid = "null"
baidu_key = os.environ.get('BAIDU_KEY')
if baidu_key == None:
    baidu_key = "null"

class TextPreprocessor:
    def __init__(self):
        self.translator = Translator(proxies=proxy)
        self.stopwords = set(STOPWORDS)
        with open(get_locale("new-stopword"), 'r') as f:
            new_data = json.load(f)
        self.stopwords.update(new_data['stopword'])

    def translate(self, text):
        translation = self.translator.translate(text, dest='en')
        return translation.text
    
    def translate_baidu(self, text):
        try:
            appid = baidu_appid
            key = baidu_key
            url = "http://api.fanyi.baidu.com/api/trans/vip/translate?q="
            salt = str(time.time())
            regex = r"[^\w\s]"
            text = re.sub(regex, "", text)
            str1 = appid + text + salt + key
            # print(str)
            sign = hashlib.md5(str1.encode('utf-8')).hexdigest()
            query = url + text + "&from=auto" + "&to=en" + "&appid=" + appid + "&salt=" + salt + "&sign=" + sign
            response = requests.get(query)
            response.raise_for_status()  # 抛出异常，如果请求失败
            print(response.text)
            data = response.json()
            if "trans_result" in data:
                translations = data["trans_result"]
                trans = ""
                for text in translations:
                    trans += text["dst"]
                print(trans)
                return trans
            else:
                print("无法翻译文本")
                return text
        except requests.exceptions.RequestException as e:
            # 处理网络请求异常
            print("请求异常:", e)
        except (KeyError, json.JSONDecodeError) as e:
            # 处理JSON解析异常
            print("JSON解析异常:", e)
        return text

    def tokenize_text(self, text):
        # text = self.translate(text)
        try:
            DetectorFactory.seed = 0
            en_flag = 0
            lang_results = detect_langs(text)
            most_probable_lang = max(lang_results, key=lambda x: x.prob)
            if most_probable_lang.lang == 'en' and most_probable_lang.prob > 0.4:
                en_flag = 1
            if en_flag == 0:
                text = self.translate_baidu(text)
        except LangDetectException as e:
            print("语言检测失败:", e)
    
        text = text.lower()
        # 去除词内特殊字符
        filtered_text = re.sub(r'[^\w]|[\d]+', '', text)
        # 无空格分词
        tokens = wordninja.split(filtered_text)
        filtered_tokens = [token for token in tokens if token not in self.stopwords and len(token) > 1]
        # POS
        tagged_words = nltk.pos_tag(filtered_tokens)
        filtered_tokens = [word for (word, pos) in tagged_words if pos.startswith('N') or pos.startswith('V')]
        return filtered_tokens

    '''
    def tokenize_text(self, text):
        # text = self.translate(text)
        tokens = word_tokenize(text.lower())
        # delete symbols
        tokens = [token for token in tokens if token.isalpha()]
        # delete stopwords
        tokens = [token for token in tokens if token not in self.stopwords]
        return tokens
    '''

    def get_top_words(self, text, num_words=10):
        tokens = self.tokenize_text(text)
        word_frequencies = {}
        for token in tokens:
            if token not in word_frequencies:
                word_frequencies[token] = 0
            word_frequencies[token] += 1

        sorted_words = sorted(word_frequencies.items(), key=lambda x: x[1], reverse=True)

        top_words = [word for word, _ in sorted_words[:num_words]]

        return top_words


class TextVectorizer:
    def __init__(self, model):  # model_path='./model/wiki-news.vec'):
        self.word2vec = model
        # 耗时： 318.149932 s

    def vectorize_word(self, word):
        word_vector = self.word2vec.get_vector(word)
        return word_vector

    def get_distance(self, word1, word2):
        distance = self.word2vec.distance(word1, word2)
        return distance

    def get_average_distances(self, list1, list2):
        avg_distances = []
        for word1 in list1:
            total_distance = 0
            len = 0
            try:
                for word2 in list2:
                    try:
                        distance = self.get_distance(word1, word2)
                        len = len + 1
                    except KeyError:
                        continue
                    total_distance += distance
                if len>0:
                    avg_distances.append(total_distance/len)
            except KeyError:
                continue
        return avg_distances

    def get_min_distances(self, list1, list2):
        min_distances = []
        for word1 in list1:
            try:
                min_distance = float('inf')
                for word2 in list2:
                    try:
                        distance = self.get_distance(word1, word2)
                        if distance < min_distance:
                            min_distance = distance
                    except KeyError:
                        continue
                if min_distance < float('inf'):
                    min_distances.append(min_distance)
            except KeyError:
                continue
        return min_distances

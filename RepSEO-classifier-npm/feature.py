import json
import re
import os
from collections import Counter
import joblib
from urllib.parse import urlparse
from db.db_init import get_locale
import pandas as pd
from word2vec import TextPreprocessor, TextVectorizer
import time
import requests
import random
from hashlib import md5
import hashlib
from langdetect import detect_langs, LangDetectException
from langdetect import DetectorFactory

baidu_appid = os.environ.get('BAIDU_APPID')
if baidu_appid == None:
    baidu_appid = "null"
baidu_key = os.environ.get('BAIDU_KEY')
if baidu_key == None:
    baidu_key = "null"

GOOGLE_ACCESS_TOKEN = os.environ.get('GOOGLE_ACCESS_TOKEN')
if GOOGLE_ACCESS_TOKEN == None:
    GOOGLE_ACCESS_TOKEN = "null"
PROJECT_NUMBER_OR_ID = os.environ.get('PROJECT_NUMBER_OR_ID')
if PROJECT_NUMBER_OR_ID == None:
    PROJECT_NUMBER_OR_ID = "null"


class FeatureExtractor:
    def __init__(self, doc, model):
        self.user_ctx_databse="npm_ctx"
        self.user_feats_databse="npm_features"
        self.doc = doc
        self.vectorizer = TextVectorizer(model)
        
        try:
            if baidu_appid != 'null' and baidu_key != 'null':
                self.doc["text_trans"] = self.translate_baidu(self.doc["text"])
            elif GOOGLE_ACCESS_TOKEN != 'null' and PROJECT_NUMBER_OR_ID != 'null':
                self.doc["text_trans"] = self.translate_google(self.doc["text"])
            else:
                self.doc["text_trans"] = self.doc["text"]
        except Exception as e:
            self.doc["text_trans"] = self.doc["text"]
            print(e)
            

        self.structure_features = self.get_structure_feature()
        
        self.semantics_features = self.get_semantic_feature()
        
        self.url_features = self.get_url_feature()
        
        self.metadata_features = self.get_metadata_feature()
        
        self.exec_features = self.total_exec_features()
        
        self.ctx_features = self.get_ctx_features()
    
    def return_semantic_features(self):
        return self.semantics_features

    def return_exec_features(self):
        return self.exec_features


    def get_structure_feature(self):
        
        '''
        结构特征：
            # of directories int 1
            Presence of introduction boolean 1
            Usage of Markdown formatting boolean 1
            Presence of code blocks boolean 1
        '''
        structure_feature = []
        
        # 目录数量
        structure_feature.append(1/(self.doc["num_dirs"]+1))
        
        # 是否有readme
        structure_feature.append(self.doc["read_me_flag"])
        
        # markdown 语法
        md_flag = 1
        if self.doc["read_me"] != '' and self.doc["read_me"] is not None:
            html_tags=['</p>', '</li>', '</ol>', '</a>', '</h1>', '</h2>', '</h3>', '</h4>',
                    '</h5>', '</h6>', '<br>']
            for tag in html_tags:
                if tag in self.doc["read_me"]:
                    md_flag = 0    
        structure_feature.append(md_flag)
        
        # Presence of code blocks
        if self.doc["read_me"] != '' and self.doc["read_me"] is not None:
            code_blocks = re.findall(r'```.*?```|~~~.*?~~~', self.doc["read_me"], re.DOTALL)
            structure_feature.append(1 / (len(code_blocks) + 1))
        else:
            structure_feature.append(1)
        
        return structure_feature
        
    def get_semantic_feature(self):
        processor = TextPreprocessor()
        keywords = processor.get_top_words(self.doc["text_trans"])
        # print(keywords)
        
        with open(get_locale("keyword-plat"), 'r') as f:
            key = json.load(f)
            platwords = key['npm']

        plat_semantics_features = self.vectorizer.get_average_distances(keywords, platwords)
        print("differences:")
        print(plat_semantics_features)

        if len(plat_semantics_features) == 0:
            return [1,1,1,1,1,1,1,1,1,1]
        
        while len(plat_semantics_features) < 10:
            random_elements = random.sample(plat_semantics_features, min(10 - len(plat_semantics_features), len(plat_semantics_features)))
            plat_semantics_features.extend(random_elements)
        return plat_semantics_features
        
        

    def get_url_feature(self):
        # get urls
        url_pattern = re.compile(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+')
        urls = url_pattern.findall(self.doc["read_me"])
        total_urls_num = len(urls)

        # load files
        with open(get_locale("keyword-url"), 'r') as f:
            key = json.load(f)
            internal_urls = key['internal-url']
            if self.doc["homepage_sub_domain"]!='' and self.doc["homepage_sub_domain"]!=None:
                internal_urls.append(self.doc["homepage_sub_domain"])
            short_urls = key['short-url']

        # with open(get_locale("keyword-media"), 'r') as f:
        #     key = json.load(f)
        #     media_suffix = key['image']  # get media suffix

        df = pd.read_csv('./db/rank_domain.csv')

        
        '''
        Ratio of internal links                  float 1
        Domain diversity of external links       int 1
        Ratio of short links                     float 1
        Avg. rank of external domains            float 1
        Duplication of links                     int 1
        '''
        
        domains_num = 0
        external_urls_num = 0
        short_urls_num = 0
        # media_urls_num = 0
        external_score = 0
        domains = set()

        for url in urls:
            try:
                domain = urlparse(url).netloc
            except ValueError as e:
                print("无效的IPv6地址: ", e)
                continue 
            domains.add(domain)
            sub_domain = ".".join(domain.split('.')[-2:])
            if sub_domain not in internal_urls:
                # if not any(internal in domains for internal in internal_urls):
                external_urls_num += 1
                # for suffix in media_suffix:
                #     if url.endswith(suffix):
                #         media_urls_num += 1
                if sub_domain in df['domain'].values:
                    rank = df[df['domain'] == sub_domain]['rank'].values[0]
                    rank_score = 1 - rank / 1000000
                    external_score += rank_score
            if sub_domain in short_urls:
                # if any(short in domains for short in short_urls):
                short_urls_num += 1

        domains_num = len(domains)  # 不同的域名
        
        element_count = Counter(urls)
        count_of_duplicates_url = sum(1 for count in element_count.values() if count > 1)

        url_features = [external_urls_num / (total_urls_num + 1),
                        1 / (domains_num + 1),
                        short_urls_num / (total_urls_num + 1),
                        external_score / (external_urls_num + 1),
                        1 / (count_of_duplicates_url + 1)
                        ]

        return url_features
    
    def get_metadata_feature(self):
        '''
            元数据：
                Copyright license boolean 1
                Repository URL boolean 1
                Homepage URL boolean 1
                Domain rank of homepage URL float 1
        '''
        metadata_feature = []
        # Copyright license
        metadata_feature.append(self.doc["license_flag"])
        
        # Repository URL
        metadata_feature.append(self.doc["repo_url_flag"])
        
        # Homepage URL
        metadata_feature.append(self.doc["homepage_flag"])
        
        # Domain rank of homepage URL
        df = pd.read_csv('./db/rank_domain.csv')
        if self.doc["homepage_sub_domain"] in df['domain'].values:
            rank = df[df['domain'] == self.doc["homepage_sub_domain"]]['rank'].values[0]
            rank_score = 1 - rank / 1000000
        else:
            rank_score = 0
        metadata_feature.append(rank_score)
        
        return metadata_feature
        
    
    def total_exec_features(self):
        return  self.structure_features + self.semantics_features + self.url_features + self.metadata_features
    
    
    def get_ctx_features(self):
        user_name = self.doc["user_name"]
        current_features = self.exec_features
        if user_name == "" or user_name is None:
            return current_features
        
        npm_history_database = joblib.load("./db/npm_history.joblib")
        target_doc = None
        for item in npm_history_database:
            if item["user_name"] ==  user_name:
                target_doc = item
        
        if target_doc is None:
            ctx_features = current_features
            npm_history_database.append({"user_name": user_name, "last1": current_features, "last2": None})
        else:
            if target_doc["last2"] is None:
                ctx_features = target_doc["last1"]
            else:
                ctx_features = [0.6*x + 0.4*y for x, y in zip(target_doc["last1"], target_doc["last2"])]
                
            for item in npm_history_database:
                if item["user_name"] ==  user_name:
                    item["last2"] = target_doc["last1"]
                    item["last1"] = current_features
                    
                    
        joblib.dump(npm_history_database,"./db/npm_history.joblib")
                    
        return ctx_features
          
    
    def total_features(self):
        total_features = self.structure_features + self.semantics_features + self.url_features + self.metadata_features + self.ctx_features
        print(total_features)
        return total_features

        
    def translate_baidu(self, text):
        try:
            try:
                DetectorFactory.seed = 0
                en_flag = 0
                lang_results = detect_langs(text)
                most_probable_lang = max(lang_results, key=lambda x: x.prob)
                if most_probable_lang.lang == 'en' and most_probable_lang.prob > 0.4:
                    return text
            except LangDetectException as e:
                print("语言检测失败:", e)
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
    

    def translate_google(self, text: str):
        try:
            headers = {
                'Authorization': f'Bearer {GOOGLE_ACCESS_TOKEN}',
                'x-goog-user-project': f'{PROJECT_NUMBER_OR_ID}',  # 替换为您的项目编号或ID
                'Content-Type': 'application/json; charset=utf-8',
            }

            data = {
                "q": text,
                "target": "en",
                "format": "text"
            }

            # 发送POST请求
            response = requests.post(
                'https://translation.googleapis.com/language/translate/v2',
                headers=headers,
                json=data
            )
            res = response.json()
            return res['data']['translations'][0]['translatedText']
        except Exception as e:
            print(e)
            return text

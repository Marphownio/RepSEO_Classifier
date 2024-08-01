import json
import re
import joblib
import numpy as np
import pandas as pd
from urllib.parse import urlparse
from db.db_init import get_locale
from word2vec import TextPreprocessor, TextVectorizer
import random
from collections import Counter

'''
docker的特征：

结构特征
Presence of introduction                 boolean 1
Usage of Markdown formatting             boolean 1
Presence of code blocks                  boolean 1


语义特征
Platform semantic distances              float 10


链接特征
Ratio of internal links                  float 1
Domain diversity of external links       int 1
Ratio of short links                     float 1
Avg. rank of external domains            float 1
Duplication of links                     int 1



元数据特征
# of Download                             int 1


用户历史行为
Historical User historical behavior float    19




'''



class FeatureExtractor:
    def __init__(self, doc, model):
        if 'namespace' in doc:
            self.author = doc['namespace']  # author_name
        else:
            self.author = ""
        if 'name' in doc:
            self.name = doc['name']  # package_name
        else:
            self.name = ""
        
        self.doc = doc
        self.model = model
        self.text = ''
        self.vectorizer = TextVectorizer(model)
        
        self.structure_features = self.get_structure_feature()
        
        self.semantics_features = self.get_semantic_feature()
        
        self.url_features = self.get_url_feature()
        
        self.metadata_features = self.get_metadata_feature()
        
        self.ctx_features = self.get_ctx_features()

    def return_semantics_features(self):
        return self.semantics_features

    def get_structure_feature(self):
        structure_feature = []
        overview = ''
        if self.doc and "name" in self.doc:
            if "full_description" in self.doc and self.doc["full_description"] is not None:
                overview = self.doc["full_description"]
        
        # Presence of introduction
        if overview != '' and overview is not None:
            structure_feature = structure_feature + [1]
        else:
            structure_feature = structure_feature + [0]
        
        
        
        # if .md or not 0代表html,1代表md
        md_flag = 0
        if overview != '' and overview is not None:
            lines = overview.split('\n')
            for line in lines:
                line = line.strip()
                if line.startswith('#') or line.startswith('* ') or line.startswith('>') \
                        or '[' in line and ']' in line and '(' in line and ')' in line:
                    md_flag = 1
            # if html tags
            html_tags=['</p>', '</li>', '</ol>', '</a>', '</h1>', '</h2>', '</h3>', '</h4>',
                    '</h5>', '</h6>', '<br>']
            for tag in html_tags:
                if tag in overview:
                    md_flag = 0    
        structure_feature = structure_feature + [md_flag]


        # num of code blocks
        code_blocks_flag = 1
        if md_flag:
            code_blocks = re.findall(r'```.*?```|~~~.*?~~~', overview, re.DOTALL)
            code_blocks_flag = 1/(len(code_blocks) + 1)
        structure_feature = structure_feature + [code_blocks_flag]
        
        
        return structure_feature
        
        
        
    def get_semantic_feature(self):
        if self.doc and "name" in self.doc:
            self.text = self.doc["name"]
            if "description" in self.doc and self.doc["description"] is not None:
                self.text += ' ' + self.doc["description"]
            if "full_description" in self.doc and self.doc["full_description"] is not None:
                self.text += ' ' + self.doc["full_description"]
        processor = TextPreprocessor()
        keywords = processor.get_top_words(self.text)
        print(keywords)
        
        with open(get_locale("keyword-plat"), 'r') as f:
            key = json.load(f)
            platwords = key['docker']
            
            
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
        urls = url_pattern.findall(self.text)
        total_urls_num = len(urls)

        # load files
        with open(get_locale("keyword-url"), 'r') as f:
            key = json.load(f)
            internal_urls = key['internal-url']
            short_urls = key['short-url']

        with open(get_locale("keyword-media"), 'r') as f:
            key = json.load(f)
            media_suffix = key['image']  # get media suffix

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
        media_urls_num = 0
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
                for suffix in media_suffix:
                    if url.endswith(suffix):
                        media_urls_num += 1
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
                        # media_urls_num / (external_urls_num + 1),
                        external_score / (external_urls_num + 1),
                        1 / (count_of_duplicates_url + 1)
                        ]

        return url_features

    def get_metadata_feature(self):
        pull_count = 0
        if self.doc and "name" in self.doc:
            if "pull_count" in self.doc and self.doc["pull_count"] is not None:
                pull_count = self.doc["pull_count"]
        return [1 / (pull_count + 1)]


    def total_features(self):
        total_features = self.structure_features + self.semantics_features + self.url_features + self.metadata_features + self.ctx_features
        print(total_features)
        return total_features
    

    def get_ctx_features(self):
        current_features = self.structure_features + self.semantics_features + self.url_features + self.metadata_features
        
        docker_history_database = joblib.load("./db/docker_history.joblib")
        
        target_doc = None
        for item in docker_history_database:
            if item["namespace"] ==  self.author:
                target_doc = item
        
        if target_doc is None:
            ctx_features = current_features
            docker_history_database.append({"namespace": self.author, "last1": current_features, "last2": None})
        else:
            if target_doc["last2"] is None:
                ctx_features = target_doc["last1"]
            else:
                ctx_features = [0.6*x + 0.4*y for x, y in zip(target_doc["last1"], target_doc["last2"])]
                
            for item in docker_history_database:
                if item["namespace"] ==  self.author:
                    item["last2"] = target_doc["last1"]
                    item["last1"] = current_features
                    
                    
        joblib.dump(docker_history_database,"./db/docker_history.joblib")
                    
        return ctx_features

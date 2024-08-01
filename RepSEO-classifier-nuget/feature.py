import json
import re
import random
import pandas as pd
from urllib.parse import urlparse
from db.db_init import get_locale
from word2vec import TextPreprocessor, TextVectorizer
import pymysql
import joblib
from collections import Counter


class FeatureExtractor:
    def __init__(self, filename, author, description, dirnums, license, readme, projectURL, repository, model):
        self.author = author  # author_name
        self.name = filename  # package_name
        self.overview = description
        self.text = filename + description
        self.text_and_readme = self.text + readme
        self.dirnums = dirnums
        self.license = license
        self.readme_tag = readme
        self.projectURL = projectURL
        self.repository = repository
        
        '''
        Structure
        # of directories int 1
        Presence of introduction boolean 1
        Usage of Markdown formatting boolean 1
        Presence of code blocks boolean 1
        
        
        
        Semantic Platform 
        semantic distances float 10
        
        
        Link
        Ratio of internal links float 1
        Domain diversity of external links int 1
        Ratio of short links float 1
        Avg. rank of external domains float 1
        Duplication of links int 1
        
        
        Metadata
        Copyright license boolean 1
        Repository URL boolean 1
        Homepage URL boolean 1
        Domain rank of homepage URL float 1
        
        
        Historical User historical behavior float 23

        '''
        
        
        self.model = model
        self.vectorizer = TextVectorizer(model)
        
        self.structure_features = self.get_structure_feature()
        
        self.semantics_features = self.get_semantic_feature()
        
        self.url_features = self.get_url_feature()
        
        self.metadata_features = self.get_metadata_feature()
        
        self.exec_features = self.total_exec_features()
        
        self.ctx_features = self.get_ctx_features()
        
    def total_features(self):
        total_features = self.structure_features + self.semantics_features + self.url_features + self.metadata_features + self.ctx_features
        print(total_features)
        return total_features
    
    def return_semantic_features(self):
        return self.semantics_features
        
        
    def total_exec_features(self):
        return  self.structure_features + self.semantics_features + self.url_features + self.metadata_features 
    
    def get_structure_feature(self):
        '''
        Structure
        # of directories int 1
        Presence of introduction boolean 1
        Usage of Markdown formatting boolean 1
        Presence of code blocks boolean 1
        '''
        structure_feats = []
        # 目录数
        structure_feats.append(1/(self.dirnums+1))
        # 是否有介绍
        if self.overview == "" or self.overview is None:
            structure_feats.append(0)
        else:
            structure_feats.append(1)
            
        # markdown 语法
        md_flag = 1
        if self.text_and_readme != '' and self.text_and_readme is not None:
            html_tags=['</p>', '</li>', '</ol>', '</a>', '</h1>', '</h2>', '</h3>', '</h4>',
                    '</h5>', '</h6>', '<br>']
            for tag in html_tags:
                if tag in self.text_and_readme:
                    md_flag = 0    
        structure_feats.append(md_flag)
        
        # Presence of code blocks
        if self.text_and_readme != '' and self.text_and_readme is not None:
            code_blocks = re.findall(r'```.*?```|~~~.*?~~~', self.text_and_readme, re.DOTALL)
            structure_feats.append(1 / (len(code_blocks) + 1))
        else:
            structure_feats.append(1)
        
        return structure_feats
        
        

    def init_db(self):
        self.mysql_db = pymysql.connect(host='10.252.176.233',
                                        port=6612,
                                        user='root',
                                        password='N0@npm',
                                        database='black_seo_bk')

    def get_semantic_feature(self):
        processor = TextPreprocessor()
        keywords = processor.get_top_words(self.text_and_readme)
        # print(keywords)
        
        with open(get_locale("keyword-plat"), 'r') as f:
            key = json.load(f)
            platwords = key['nuget']

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
        urls = url_pattern.findall(self.text_and_readme)
        total_urls_num = len(urls)

        # load files
        with open(get_locale("keyword-url"), 'r') as f:
            key = json.load(f)
            internal_urls = key['internal-url']
            if self.projectURL!='' and self.projectURL!=None:
                internal_urls.append(self.projectURL)
                
            short_urls = key['short-url']


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
        Copyright license boolean 1
        Repository URL boolean 1
        Homepage URL boolean 1
        Domain rank of homepage URL float 1
        '''
        metadata_feature = []
        # Copyright license
        metadata_feature.append(self.license)
        
        # Repository URL
        if self.repository is not None and self.repository != "":
            metadata_feature.append(1)
        else:
            metadata_feature.append(0)
        
        # Homepage URL
        if self.projectURL is not None and self.projectURL != "":
            metadata_feature.append(1)
        else:
            metadata_feature.append(0)
        
        # Domain rank of homepage URL
        df = pd.read_csv('./db/rank_domain.csv')
        if self.projectURL in df['domain'].values:
            rank = df[df['domain'] == self.projectURL]['rank'].values[0]
            rank_score = 1 - rank / 1000000
        else:
            rank_score = 0
        metadata_feature.append(rank_score)
        
        return metadata_feature
    
    
    def get_ctx_features(self):
        current_features = self.exec_features
        author = self.author
        if author == "" or author is None:
            return current_features

        nuget_history_database = joblib.load("./db/nuget_history.joblib")
        target_doc = None
        for item in nuget_history_database:
            if item["author"] ==  author:
                target_doc = item
        
        if target_doc is None:
            ctx_features = current_features
            nuget_history_database.append({"author": author, "last1": current_features, "last2": None})
        else:
            if target_doc["last2"] is None:
                ctx_features = target_doc["last1"]
            else:
                ctx_features = [0.6*x + 0.4*y for x, y in zip(target_doc["last1"], target_doc["last2"])]
                
            for item in nuget_history_database:
                if item["author"] ==  author:
                    item["last2"] = target_doc["last1"]
                    item["last1"] = current_features
                    
                    
        joblib.dump(nuget_history_database,"./db/nuget_history.joblib")
                    
        return ctx_features
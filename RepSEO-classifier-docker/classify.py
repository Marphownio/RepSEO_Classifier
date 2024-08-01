import joblib
from gensim.models import KeyedVectors
import os
from feature import FeatureExtractor
import time
import time
import pandas as pd


WIKI_PATH = os.environ.get('WIKI_PATH')
if WIKI_PATH == None:
    print("Please set WIKI_PATH!")
    exit(0)

class classify:
    def __init__(self) -> None:
        self.docker_official_database = joblib.load("./db/docker_official.joblib")
    
    def load_model(self): 
        # load the word2vec
        print("start loading")
        self.word2vec = KeyedVectors.load_word2vec_format(WIKI_PATH) 
        print("finished")
        # load the classifier
        self.classifier = joblib.load('./model/RFC.joblib')
        
        
    def load_test_case(self):
        document_list = []
        label_list = []
        name_list = []
        directory = "./test_case"
        for file in os.listdir(directory):
            file_path = os.path.join(directory, file)
            this_file = joblib.load(file_path)
            document_list.append(this_file["doc"])
            name_list.append(this_file["name"])
            label_list.append(this_file["label"])
        
        return name_list,label_list,document_list
        

    def record_result(self,name_list,label_list,pred_list):
        timestamp = str(time.time())
        directory = "./result"
        df = pd.DataFrame({
            "name":name_list,
            "label":label_list,
            "pred":pred_list,
        })
        
        if not os.path.exists(directory):
            os.makedirs(directory)
        df.to_csv(directory+"/result_"+timestamp+".csv",index=False)
        
    def if_official(self,slug):
        for item in self.docker_official_database:
            if item["slug"] == slug:
                return True
        return False

    def analysis(self):
        name_list,label_list,document_list = self.load_test_case()
        pred_list = []

        for item in document_list:
            # check if no overview
            if "full_description" not in item or item["full_description"]=="" or item["full_description"] is None:
                pred_list.append("non-abuse")
                continue
            
            # check if official
            slug = ''
            if "namespace" in item and "name" in item:
                slug = item["namespace"] + "/" + item['name']
            if self.if_official(slug):
                pred_list.append("non-abuse")
                continue

            features = []
            extractor = FeatureExtractor(item, self.word2vec)
            features.append(extractor.total_features())
            label_pred = self.classifier.predict(features)
            pred_list.append(label_pred)
            
        self.record_result(name_list,label_list,pred_list)
                
                
if __name__ == "__main__":
    classifier = classify()
    classifier.load_model()
    classifier.analysis()
    
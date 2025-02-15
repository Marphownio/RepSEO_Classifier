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
        # load test case for classification
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
        # function to store final classification result
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
        # to check if a docker image is official
        for item in self.docker_official_database:
            if item["slug"] == slug:
                return True
        return False

    def analysis(self):
        # function to get package's information, feature and perform classification
        name_list,label_list,document_list = self.load_test_case()
        pred_list = []

        # classify the packages to be tested in sequence.
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

            # extrate features form information and metadata got before
            extractor = FeatureExtractor(item, self.word2vec)
            features.append(extractor.total_features())

            # use feature to perform classification
            label_pred = self.classifier.predict(features)
            pred_list.append(label_pred)
            
        self.record_result(name_list,label_list,pred_list)
                
                
if __name__ == "__main__":
    classifier = classify()
    classifier.load_model()
    classifier.analysis()
    
import joblib
from gensim.models import KeyedVectors
import os
from feature import FeatureExtractor
import time
import time
import pandas as pd
from file_extractor import FilePreprocessor

WIKI_PATH = os.environ.get('WIKI_PATH')
if WIKI_PATH == None:
    print("Please set WIKI_PATH!")
    exit(0)

class classify:
    def __init__(self) -> None:
        pass
    
    def load_model(self): 
        # load the word2vec
        print("start loading")
        self.word2vec = KeyedVectors.load_word2vec_format(WIKI_PATH) 
        # self.word2vec = None
        print("finished")
        # load the classifier
        self.classifier = joblib.load('./model/RFC.joblib')
        
        
    def load_test_case(self):
        path_list = []
        label_list = []
        name_list = []
        non_abuse_directory = "./test_case/non-abuse"
        for file in os.listdir(non_abuse_directory):
            file_path = os.path.join(non_abuse_directory, file)
            name_list.append(file)
            path_list.append(file_path)
            label_list.append("non-abuse")
            
            
        abuse_directory = "./test_case/abuse"
        for file in os.listdir(abuse_directory):
            file_path = os.path.join(abuse_directory, file)
            name_list.append(file)
            path_list.append(file_path)
            label_list.append("abuse")
            
        
        return name_list,path_list,label_list
        

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


    def analysis(self):
        name_list,path_list,label_list = self.load_test_case()
        pred_list = []

        for filename,path in zip(name_list,path_list):
            processor = FilePreprocessor(filename,path)
            author, description, dirnum, license, readme, projectURL, repository, error_flag = processor.extract_info()
            extractor = FeatureExtractor(filename, author, description, dirnum, license, readme, projectURL, repository, self.word2vec)
            features = []
            features.append(extractor.total_features())
            label_pred = self.classifier.predict(features)
            pred_list.append(label_pred)
            
        self.record_result(name_list,label_list,pred_list)
                
                
if __name__ == "__main__":
    classifier = classify()
    classifier.load_model()
    classifier.analysis()
    
import joblib
from gensim.models import KeyedVectors
import os
from feature import FeatureExtractor
import time
import time
import pandas as pd
from file_extractor import FileExtractor

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
        print("finished")
        # load the classifier
        self.classifier = joblib.load('./model/RFC.joblib')
        
        
    def load_test_case(self):
        # load test case for classification
        tar_file_list = []
        json_file_list = []
        label_list = []
        name_list = []
        non_abuse_directory = "./test_case/non-abuse"
        for file in os.listdir(non_abuse_directory):
            file_path = os.path.join(non_abuse_directory, file)
            if file_path.endswith('.tgz'):
                tar_file_list.append(file_path)
                name_list.append(file)
                label_list.append("non-abuse")
            if file_path.endswith('.tgz.json'):
                json_file_list.append(file_path)
            
            
        abuse_directory = "./test_case/abuse"
        for file in os.listdir(abuse_directory):
            file_path = os.path.join(abuse_directory, file)
            if file_path.endswith('.tgz'):
                tar_file_list.append(file_path)
                name_list.append(file)
                label_list.append("abuse")
            if file_path.endswith('.tgz.json'):
                json_file_list.append(file_path)
            
        
        return name_list,label_list,tar_file_list,json_file_list
        

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


    def analysis(self):
        # function to get package's information, feature and perform classification
        name_list,label_list,tar_file_list,json_file_list = self.load_test_case()
        pred_list = []

        # classify the packages to be tested in sequence.
        for tar_file_path,json_file_path,name in zip(tar_file_list,json_file_list,name_list):\
            # get raw file information and metadata
            file_extracor = FileExtractor(tar_file_path,json_file_path,name)
            doc = file_extracor.get_doc()

            # If no descriptive text is present, no classification will be performed.
            if doc["text"].strip() == None or doc["text"].strip() == '':
                pred_list.append("non-abuse")
                continue
            features = []

            # extrate features form information and metadata got before
            extractor = FeatureExtractor(doc, self.word2vec)
            features.append(extractor.total_features())

            # use feature to perform classification
            label_pred = self.classifier.predict(features)
            pred_list.append(label_pred)
            
        self.record_result(name_list,label_list,pred_list)
                
                
if __name__ == "__main__":
    classifier = classify()
    classifier.load_model()
    classifier.analysis()
    
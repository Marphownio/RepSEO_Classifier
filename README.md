# ***RepSEO*** Classifier

This is the official repository for our IEEE/ACM ICSE'25 [paper](RepSEO.pdf): 
> Mengying Wu, Geng Hong, Wuyuao Mai, Xinyi Wu, Lei Zhang, Yingyuan Pu, Huajun Chai, Lingyun Ying, Haixin Duan, Min Yang. *Exposing the Hidden Layer: Software Repositories in the Service of SEO Manipulation*. IEEE/ACM ICSE'25

*Blackhat Search Engine Optimization through REPositories (**RepSEO**)* is a novel attack vector where attackers carefully craft packages to manipulate search engine results, exploiting the credibility of software repositories to promote illicit websites.

RepSEO Classifier is the tool to detected those abusive packages in npm, Nuget, Docker Hub. 

The attackers and our classifier focus on the **homepage** of packages, which are indexed by search engines. Thus, RepSEO packages often conspicuously display promotional content, which is typically illicit and **distinct** from other packages in the same software repositories. As promotion links are the core of SEO, the classifier also focuses on the **usage of links**, especially short links and unpopular links. Furthermore, attackers may upload multiple RepSEO packages using a single account considering **registration costs**, thus we consider historical behavior. We also model a benign package from their rich structure and metadata.

In sum, the classifiers include features from five aspects: structure, semantics, links, metadata, and historical behavior.The summary of features is shown below.The complete feature definition and details of feature engineering can be found in [Appendix_of_RepSEO.pdf](Appendix_of_RepSEO.pdf).

| Type       | Feature                            | Data Type | Length |
|------------|------------------------------------|-----------|--------|
| **Structure** | \# of directories                | int       | 1      |
|            | Presence of introduction            | boolean   | 1      |
|            | Usage of HTML formatting            | boolean   | 1      |
|            | Presence of code blocks             | boolean   | 1      |
| **Semantic** |Platform semantic distances        | float     | 10     |
| **Link**   | Ratio of internal links             | float     | 1      |
|            | Domain diversity of external links  | int       | 1      |
|            | Ratio of short links                | float     | 1      |
|            | Avg. rank of external domains       | float     | 1      |
|            | Duplication of links                | int       | 1      |
| **Metadata** | Copyright license                 | boolean   | 1      |
|            | Official artifact                   | boolean   | 1      |
|            | Repository URL                      | boolean   | 1      |
|            | Homepage URL                        | boolean   | 1      |
|            | Domain rank of homepage URL         | float     | 1      |
|            | \# of Download                      | int       | 1      |
| **Historical** |User historical behavior         | float     | 25     |


## Setup

Base environment requirement:
- Linux 
- python: 3.8
- 10GB or more of disk space

Download our artifacts by:
```shell
git clone https://github.com/Marphownio/RepSEO_Classifier.git
cd ./RepSEO_Classifier
```
### Step 1. Prepare Docker Environment
To avoid any impact on the host machine from the code execution, it is recommended to use our artifacts in Docker container. Before building the image, please ensure that docker-related dependencies are installed on your computer. 

Build docker image.
```shell
docker build -t repseo_classifier .
```
Then enter docker container.
```shell
docker run -it --name repseo repseo_classifier bash -c "cd /RepSEO_Classifier && bash"
```
Please note that the following steps will all be executed inside the docker container.

### Step 2. Apply for Translate API *(Optional)*

Translate API is needed to help ***RepSEO*** classifier better understand the semantic context of packages. You can choose to apply for one of the following translate API.
- Google Translate. Click [here](https://cloud.google.com/translate/docs/overview) and get Google Cloud's `Access token` and `Project number or id`.
- Baidu Translate. Click [here](https://api.fanyi.baidu.com/) and get Baidu's `AppID` and `Key`.


## Usage

*RepSEO* classifier is consist of 3 sub-classifiers respectively for npm, NuGet and Docker Hub, all of which are of the same usage. We have prepared relevant test cases as input for the classifier. Each test case includes the metadata from the packages as well as their source files. For each repository, 25 abusive packages and 25 non-abusive packages are prepared and saved in their respective directories.

- `./RepSEO-classifier-npm/test_case/`
- `./RepSEO-classifier-nuget/test_case/`
- `./RepSEO-classifier-docker/test_case/`

The output of the classifier is the classification result for all test cases, and each test case will be labeled as `abuse` or `non-abuse`. Since the usage for all classifiers is the same, here we take the classifier for npm as an example. 

Change to subdirectory of npm *RepSEO* classifier.
``` shell
cd ./RepSEO-classifier-npm/
```
Export environment variables for translate API *(Optional)* . Skip this step if you do not apply for any translation API.
``` shell
# If you chose Baidu for translation
export BAIDU_APPID=<Your AppID of Baidu Translate API>
export BAIDU_KEY=<Your Key of Baidu Translate API>

# If you chose Google Cloud for translation
export GOOGLE_ACCESS_TOKEN=<Your Access Token of Google Cloud Translate API>
export PROJECT_NUMBER_OR_ID=<Your Number or ID of Google Cloud Translate API Project>
```
Run the *RepSEO* classifier.
``` shell
python3 classify.py
```
Please note that loading the Word2Vec model may take some time. The expected runtime for each classifier to process the test cases is approximately `6` minutes.

## Result
The results generated by all three classifiers are saved in their respective directories as a csv file.

``` text
./RepSEO-classifier-npm/result/result_<time_stamp>.csv
./RepSEO-classifier-nuget/result/result_<time_stamp>.csv
./RepSEO-classifier-docker/result/result_<time_stamp>.csv
```
The csv files are saved in the format like
``` text
name,label,pred
<package_name>,<package_label>,<predication_by_classifier>
```

## Data

### Abusive Packages List
After conducting detection on the entire dataset, our tool discovered a total of 3,801,682 ***RepSEO*** packages in npm, NuGet, Docker Hub. Details are listed in the following directories respectively. To meet the file size limitation, the CSV file is split into multiple sub chunks.
``` text
./RepSEO-package-list/npm/
./RepSEO-package-list/nuget/
./RepSEO-package-list/docker/
```

## Project Structure
```shell
├── README.md
├── RepSEO.pdf                                
├── Appendix_of_RepSEO.pdf
├── download_word2vec_model.sh        # Runtime environment setup file
├── download_tranco_list.py           # Runtime environment setup file
├── download_nltk_model.py            # Runtime environment setup file
├── Dockerfile                        # Runtime environment setup file
├── RepSEO-package-list               # Lists of all detected abusive packages
│   ├── npm
│   │   ├── ......
│   ├── nuget
│   │   ├── ......
│   ├── docker
│   │   ├── ......
├── RepSEO-classifier-npm               # Files of npm classifier
│   ├── ......
├── RepSEO-classifier-nuget             # Files of NuGet classifier
│   ├── ......
├── RepSEO-classifier-docker            # Files of Docker classifier
│   ├── db                                 # Local database
│   │   ├── db_init.py
│   │   ├── docker_history.joblib          
│   │   ├── docker_official.joblib
│   │   ├── keyword-media.json
│   │   ├── keyword-plat.json
│   │   ├── keyword-url.json
│   │   ├── keyword-word.json
│   │   ├── locale_config.py
│   │   ├── new-stopword.json
│   │   └── rank_domain.csv
│   ├── model                              # Model of pre-trained classifier model
│   │   └── RFC.joblib                  
│   ├── result                             # Output files of classifier
│   │   └── ......
│   ├── test_case                          # Test cases(input) of classifier
│   │   └── ......
│   ├── classify.py                        # Entry point of classifier
│   ├── feature.py                         # Feature extraction Tool
│   ├── file_extractor.py                  # Compression package analyzer
│   └── word2vec.py                        # Code for Word2vec Model
```
> *The directory structure of the 3 classifiers is the same, so we will not elaborate further.* 
### Code File Illustration
- `classify.py`: Entry point and core implementation of each classifier.
- `file_extractor.py`: Extract the source information from the compressed package file (for npm and NuGet).
- `word2vec.py`: Perform vectorization on the extracted text-based source information.
- `feature.py`: Extract the features required by the classifier from the source information.

### Directory Illustration
- `db`: Used as a local database to store essential information supporting the classifier, including platform-specific keywords, database configurations, user history, domain rankings, and more.
- `model`: Include the source files of the pre-trained classification model.
- `test_case`: Include pre-prepared test cases, which serve as inputs for the model. Each test case includes the metadata from the packages as well as their source files.
- `result`: Store the outputs of the classifier.

## Citation

If you find our work helpful, we would greatly appreciate it if you could cite our paper using the following BibTeX format.
```text
@inproceedings{wu2025seo,
  author    = {Mengying Wu and Geng Hong and Wuyuao Mai and Xinyi Wu and Lei Zhang and Yingyuan Pu and Huajun Chai and Lingyun Ying and Haixin Duan and Min Yang},
  title     = {Exposing the Hidden Layer: Software Repositories in the Service of SEO Manipulation},
  year      = {2025}, 
  booktitle = {Proceedings of the IEEE/ACM 47th International Conference on Software Engineering},
}
```
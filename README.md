# ***RepSEO*** Classifier

This is the official repository for our IEEE/ACM ICSE'25 [paper](RepSEO.pdf): 
> Mengying Wu, Geng Hong, Wuyuao Mai, Xinyi Wu, Lei Zhang, Yingyuan Pu, Huajun Chai, Lingyun Ying, Haixin Duan, Min Yang. *Exposing the Hidden Layer: Software Repositories in the Service of SEO Manipulation*. IEEE/ACM ICSE'25 paper

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

Base Environment:
- Linux 
- python: 3.8

Download our artifacts by:
```shell
git clone git@github.com:Marphownio/RepSEO_Classifier.git
cd ./RepSEO_Classifier
```
### Step 0. Prepare Docker Environment (*Recommand, Optional*)
To avoid any impact on the host machine from the code execution, it is recommended to use our artifacts in Docker container. Before building the image, please ensure that docker-related dependencies are installed on your computer. 

Build a Python environment in docker.
```shell
docker pull python:3.8
```
Then instantiate a container from the docker image.
```shell
docker run -it -d --name repseo-classifier python:3.8 /bin/bash
```
Copy source code to the container.
```shell
docker cp . repseo-classifier:/RepSEO_Classifier
```
Access the docker container and switch to the working directory.
```shell
docker exec -it repseo-classifier /bin/bash -c "cd /RepSEO_Classifier && bash"
```
Note if you use docker in this step, the following operations are executed within docker container.

### Step 1. Installing Python Dependencies

``` shell
pip3 install -r requirements.txt
```

### Step 2. Download Word2Vec Model

Manually download the [Word2Vec Model](https://dl.fbaipublicfiles.com/fasttext/vectors-wiki/wiki.en.zip), which is trained on Wikipedia using fastText, or use the command.
``` shell
wget https://dl.fbaipublicfiles.com/fasttext/vectors-wiki/wiki.en.zip
```
And then unzip it to get the `.vec` model.

### Step 3. Download Tranco List

[Tranco](https://tranco-list.eu/) list of domain rank helps when detecting ***RepSEO*** packages. Download it by using the script.
``` shell
python3 download_tranco_list.py
```

### Step 4. Download NLTK Model
An NLTK model to download for natural language processing.
``` shell
python3 download_nltk_model.py
```


### Step 5. Apply for Baidu Translate API *(Optional)*

Translate API is needed to help ***RepSEO*** classifier better understand the semantic context of packages. Click to apply for [Baidu Translate API](https://api.fanyi.baidu.com/) and get your AppID and Key.

## Usage

*RepSEO* classifier is consist of 3 sub-classifiers respectively for npm, NuGet and Docker Hub, all of which are of the same usage. Here we take the classifier for npm as an example.

Change to subdirectory of npm *RepSEO* classifier.
``` shell
cd ./RepSEO-classifier-npm/
```
Export environment variables for Word2Vec Model you save in Step 2.
``` shell
export WIKI_PATH=/path/to/wiki.en.vec
```
Export environment variables for Baidu Translate API *(Optional)* .
``` shell
export BAIDU_APPID=<AppID of Baidu Translate API>
export BAIDU_KEY=<Key of Baidu Translate API>
```
Run the *RepSEO* classifier.
``` shell
python3 classify.py
```
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

### Test Cases

25 abusive packages and 25 non-abusive packages are prepared respectively for npm, NuGet and Docker Hub, which are saved in their respective directories.
``` text
./RepSEO-classifier-npm/test_case/
./RepSEO-classifier-nuget/test_case/
./RepSEO-classifier-docker/test_case/
```

### Abusive Packages List
After conducting detection on the entire dataset, our tool discovered a total of 3,801,682 ***RepSEO*** packages in npm, NuGet, Docker Hub. Details are listed in the following directories respectively. To meet the file size limitation, the CSV file is split into multiple sub chunks.
``` text
./RepSEO-package-list/npm/
./RepSEO-package-list/nuget/
./RepSEO-package-list/docker/
```

## Project Structure
```
├── RepSEO.pdf
├── Appendix_of_RepSEO.pdf
├── download_tranco_list.py
├── download_nltk_model.py
├── README.md
├── RepSEO-package-list
│   ├── npm
│   │   ├── ......
│   ├── nuget
│   │   ├── ......
│   ├── docker
│   │   ├── ......
├── RepSEO-classifier-npm
│   ├── ......
├── RepSEO-classifier-nuget
│   ├── ......
├── RepSEO-classifier-docker
│   ├── db
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
│   ├── model
│   │   └── RFC.joblib
│   ├── result
│   │   └── ......
│   ├── test_case
│   │   └── ......
│   ├── classify.py
│   ├── feature.py
│   ├── file_extractor.py
│   └── word2vec.py
```

### Code Illustration
- `classify.py`: Entry point of each classifier
- `feature.py`: Feature extraction Tool
- `file_extractor.py`: Analyze compression package (for npm and NuGet)
- `word2vec.py`: Code for Word2vec Model


## Citation
```text
@inproceedings{wu2025seo,
  author    = {Mengying Wu and Geng Hong and Wuyuao Mai and Xinyi Wu and Lei Zhang and Yingyuan Pu and Huajun Chai and Lingyun Ying and Haixin Duan and Min Yang},
  title     = {Exposing the Hidden Layer: Software Repositories in the Service of SEO Manipulation},
  year      = {2025}, 
  booktitle = {Proceedings of the IEEE/ACM 47th International Conference on Software Engineering},
}
```
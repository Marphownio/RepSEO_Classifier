# ***RepSEO*** Classifier

*Blackhat Search Engine Optimization through REPositories (**RepSEO**)* is a novel attack vector where attackers carefully craft packages to manipulate search engine results, exploiting the credibility of software repositories to promote illicit websites.

RepSEO Classifier is the tool to detected those abusive packages in npm, Nuget, Docker Hub.
The details of feature engineering can be found in [Appendix_of_RepSEO.pdf](Appendix_of_RepSEO.pdf).

## Base Environment
- Linux 
- python: 3.8 or higher

## Installation

### Step 1. Installing Python Dependencies
``` shell
pip3 install -r requirements.txt
```

### Step 2. Download Word2Vec Model

Manually download the [Word2Vec Model](https://dl.fbaipublicfiles.com/fasttext/vectors-wiki/wiki.en.zip), which is trained on Wikipedia using fastText, or use the command like
``` shell
wget https://dl.fbaipublicfiles.com/fasttext/vectors-wiki/wiki.en.zip
```

### Step 3. Download Tranco List

[Tranco](https://tranco-list.eu/) list of domain rank helps when detecting ***RepSEO*** packages. Download it by using the script
``` shell
python3 download_tranco_list.py
```


### Step 4. Apply for Baidu Translate API *(Optional)*

Translate API is needed to help ***RepSEO*** classifier better understand the semantic context of packages. Click to apply for [Baidu Translate API](https://api.fanyi.baidu.com/) and get your AppID and Key.

## Usage

***RepSEO*** classifier is consist of 3 sub-classifiers respectively for npm, NuGet and Docker Hub, all of which are of the same usage. Here we take the classifier for npm as an example.

Change to subdirectory of npm ***RepSEO*** classifier.
``` shell
cd ./RepSEO-classifier-npm/
```
Export environment variables for Word2Vec Model.
``` shell
export WIKI_PATH=<the path of the Word2Vec Model you save in Step 2>
```
Export environment variables for Baidu Translate API *(Optional)* .
``` shell
export BAIDU_APPID=<AppID of Baidu Translate API>
export BAIDU_KEY=<Key of Baidu Translate API>
```
Run the ***RepSEO*** classifier.
``` shell
python3 classify.py
```

## Results
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

## Test Cases

25 abusive packages and 25 non-abusive packages are prepared respectively for npm, NuGet and Docker Hub, which are saved in their respective directories.
``` text
./RepSEO-classifier-npm/test_case/
./RepSEO-classifier-nuget/test_case/
./RepSEO-classifier-docker/test_case/
```

## Abusive Packages List
After conducting detection on the entire dataset, our tool discovered a total of 3,801,682 ***RepSEO*** packages in npm, NuGet, Docker Hub. Details are listed in RepSEO-package-list for [npm](./RepSEO-package-list/npm), [NuGet](./RepSEO-package-list/nuget) and [Docker Hub](./RepSEO-package-list/docker) respectively. To meet the file size limitation of Anonymous Github, the CSV file is split into multiple sub chunks.

## Project Structure

```
├── Appendix_of_RepSEO.pdf
├── download_tranco_list.py
├── README.md
├── RepSEO-classifier-npm
│   ├── ......
├── RepSEO-classifier-nuget
│   ├── ......
├── RepSEO-classifier-docker
│   ├── db
│   │   ├── db_init.py
│   │   ├── docker_history.joblib
│   │   ├── docker_official.joblib
│   │   ├── keyword-ibt.json
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
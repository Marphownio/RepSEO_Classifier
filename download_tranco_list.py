import requests
import zipfile
import io
import pandas as pd

def download_and_extract_csv_from_zip(url, column_names):
    response = requests.get(url)
    if response.status_code != 200:
        raise Exception(f"Failed to download file: {response.status_code}")
    
    with zipfile.ZipFile(io.BytesIO(response.content)) as z:
        file_list = z.namelist()
        
        csv_filename = None
        for file in file_list:
            if file.endswith('.csv'):
                csv_filename = file
                break
        
        if csv_filename is None:
            raise Exception("No CSV file found in the ZIP archive")
        
        with z.open(csv_filename) as f:
            df = pd.read_csv(f,header=None)
    
    df.columns = column_names
    
    return df



url = "https://tranco-list.eu/download_daily/Z377G"
column_names = ['rank','domain']

df = download_and_extract_csv_from_zip(url, column_names)

df.to_csv("./RepSEO-classifier-docker/db/rank_domain.csv",index=False)
df.to_csv("./RepSEO-classifier-npm/db/rank_domain.csv",index=False)
df.to_csv("./RepSEO-classifier-nuget/db/rank_domain.csv",index=False)

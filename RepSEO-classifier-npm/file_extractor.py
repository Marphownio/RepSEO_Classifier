from urllib.parse import urlparse
import tarfile
import json
import re

class FileExtractor:
    def __init__(self, tarfile_path, jsonfile_path, tarname) -> None:
        self.tarfile_path = tarfile_path
        self.jsonfile_path = jsonfile_path
        self.tarname = tarname
        self.doc = {
            "name":"",
            "tarname":tarname,
            "des":"",
            "homepage_sub_domain":"",
            "homepage_flag":0,
            "repo_url_flag":0,
            "read_me":"",
            "read_me_flag":0,
            "license_flag" : 0,
            "num_dirs":0,
            "user_name":"",
            "user_email":"",
            "text":"",
            "text_trans":"",
            }
        self.extract_tarfile()
        
    def extract_tarfile(self):
        name=self.tarname.rstrip('\n')

        # name des homepage repourl等字段
        try:
            targetjson_file_path = "package/package.json"  # 需要读取的文件在.tar包中的路径
            # 打开.tar包
            with tarfile.open(self.tarfile_path, "r") as tar:
                # 检查.tar包中是否存在指定路径的文件
                if targetjson_file_path in tar.getnames():
                    # 获取指定路径文件的File对象
                    file = tar.extractfile(targetjson_file_path)
                    
                    # 读取文件内容
                    try:
                        json_text = file.read().decode("utf-8")
                        content = json.loads(json_text)
                        
                        if 'name' in content:
                            self.doc["name"] = content['name']

                            
                        if 'description' in content:
                            self.doc["des"] = content['description']

                            
                        if 'homepage' in content and content["homepage"]!="":
                            self.doc["homepage_flag"] = 1
                            domain = urlparse(content['homepage']).netloc
                            self.doc["homepage_sub_domain"] = ".".join(domain.split('.')[-2:])


                        if 'repository' in content and 'url' in content['repository'] and content['repository']['url']!="":
                            self.doc["repo_url_flag"] = 1
                            
                            
                    except Exception as reason:
                        print(reason)
                    
        except Exception as reason:
            print(reason)
        

            
        # 再读readme、 子目录数量
        
        try:
            rdm_file_path1 = "package/README.md"
            rdm_file_path2 = "package/readme.md"
            rdm_file_path3 = "package/Readme.md"
            rdm_file_path4 = "package/README.MD"
            lisence_path = "package/LISENCE"
            target_file_path = ""  # 需要读取的文件在.tar包中的路径
            # 打开.tar包
            with tarfile.open(self.tarfile_path, "r") as tar:
                # 检查.tar包中是否存在指定路径的文件
                if rdm_file_path1 in tar.getnames():
                    target_file_path = rdm_file_path1
                elif rdm_file_path2 in tar.getnames():
                    target_file_path = rdm_file_path2
                elif rdm_file_path3 in tar.getnames():
                    target_file_path = rdm_file_path3
                elif rdm_file_path4 in tar.getnames():
                    target_file_path = rdm_file_path4
                    
                if lisence_path in tar.getnames():
                    self.doc["license_flag"]=1
                
             
             
                try:
                    num_dirs = 0
                    for member in tar.getmembers():
                        # 检查成员是否为目录
                        if member.isdir():
                            num_dirs += 1
                    self.doc["num_dirs"] = num_dirs
                except Exception as reason:
                    print(reason)
                
                latin_flag = 0
                if target_file_path in tar.getnames():
                    try:
                        # 获取指定路径文件的File对象
                        file = tar.extractfile(target_file_path)
                        # 读取文件内容
                        self.doc["read_me"] = file.read().decode("utf-8").strip()
                    except Exception as reason:
                        print(reason)
                        latin_flag=1
                        
                    
                    if latin_flag==1:
                        try:
                            # 获取指定路径文件的File对象
                            file = tar.extractfile(target_file_path)
                            # 读取文件内容
                            self.doc["read_me"] = file.read().decode("Latin-1").strip()
                        except Exception as reason:
                            print(reason)

        except Exception as reason:
            print(reason)
        finally:
            # 如果readme实在是太短了就不分类了(目前认为redme为空则不分类)
            if len(self.doc["read_me"].strip())>1:
                self.doc["read_me_flag"] = 1
                    
                    
            
        try:
            self.doc["text"] = self.doc["name"] + ' ' + self.doc["des"] + ' ' + self.doc["read_me"]
        except Exception as reason:
            self.doc["text"] = self.doc["read_me"]
            
        self.doc["text_trans"] = self.doc["text"]
            
        # 读取user的 name 与 email 字段
        tar_json_f = None
        try:
            tar_json_f = open(self.jsonfile_path, 'r', errors='ignore')
            tar_json=tar_json_f.read()
            pattern = r"'_npmUser'.*?}"
            match = re.search(pattern, tar_json)
            if match:
                matched_string = match.group()
                match_array = matched_string.split("'")
                self.doc["user_name"] = match_array[5]
                self.doc["user_email"] = match_array[9]

        except Exception as e:
            print(e)
        finally:
            if tar_json_f in locals():
                tar_json_f.close()
                
                
    def get_doc(self):
        # print(self.doc)
        return self.doc
    
# if __name__=="__main__":
#     a = TarfileExtractor('','',"test1.tar")
#     a.get_doc()
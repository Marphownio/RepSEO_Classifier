import zipfile
import os
import glob
import re
from urllib.parse import urlparse


class FilePreprocessor:
    def __init__(self, filename, path):
        self.file = filename
        self.path = path
        self.dir = './test_case/release/' + filename
        if not os.path.exists('./test_case/release'):
            os.makedirs('./test_case/release')
        self.author = ''
        self.description = ''
        self.readme = ''
        self.projectURL = ''
        self.repository = ''
        self.dirnum = 0
        self.license = 0
        self.metadata = ''

    def unzip(self):
        # 打开zip文件
        file_path = self.path
        try:
            with zipfile.ZipFile(file_path, 'r') as zip_file:
                directories = set()
                for file_info in zip_file.infolist():
                    # 提取文件名及其路径
                    file_path = file_info.filename
                    # print(file_path)
                    if file_path.endswith('/'):
                        # 获取目录路径
                        directory = '/'.join(file_path.split('/')[:-1])
                        directories.add(directory)
                    # 排除空目录，并返回目录数量
                self.dirnum = len(directories - {''})
                # 解压全部文件到指定目录
                for file in zip_file.namelist():
                    if file.endswith('.nuspec') or file.endswith('.md'):
                        zip_file.extract(file, self.dir)
                return 0
        except Exception as e:
            print(e)
            return 1

    def get_content(self):
        metadata = ''
        readme = ''
        # 读取解压后的文件内容
        folder_path = self.dir  # 指定文件夹路径
        for file_path in glob.glob(folder_path + '/*.nuspec'):
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    metadata = f.read()
            except UnicodeDecodeError:
                try:
                    with open(file_path, 'r', encoding='utf-16') as f:
                        metadata = f.read()
                except UnicodeDecodeError:
                    print("UnicodeDecodeError: 无法解码nuspec文件", self.file)
                    name = self.file + '\n'
                    with open("nuspec_error.txt", "a") as file:
                        file.write(name)

        readme_tag = 0
        if os.path.isfile(os.path.join(folder_path, 'readme.md')):
            try:
                # 读取 readme.md 文件内容
                with open(os.path.join(folder_path, 'readme.md'), 'r') as file:
                    readme = file.read()
                    # print(readme)
                    if readme != ' ':
                        readme_tag = 1
                        name = self.file +'\n'
            except UnicodeDecodeError:
                print("UnicodeDecodeError: 无法解码readme文件", self.file)
                name = self.file +'\n'
                with open("readme_error.txt", "a") as file:
                    file.write(name)
        
        if os.path.isfile(os.path.join(folder_path, 'Readme.md')):
            try:
                # 读取 readme.md 文件内容
                with open(os.path.join(folder_path, 'Readme.md'), 'r') as file:
                    readme = file.read()
                    # print(readme)
                    if readme != ' ':
                        readme_tag = 1
                        name = self.file +'\n'
            except UnicodeDecodeError:
                print("UnicodeDecodeError: 无法解码Readme文件", self.file)
                name = self.file +'\n'
                with open("readme_error.txt", "a") as file:
                    file.write(name)
        
        if os.path.isfile(os.path.join(folder_path, 'README.md')):
            try:
                # 读取 readme.md 文件内容
                with open(os.path.join(folder_path, 'README.md'), 'r') as file:
                    readme = file.read()
                    # print(readme)
                    if readme != ' ':
                        readme_tag = 1
                        name = self.file +'\n'
            except UnicodeDecodeError:
                print("UnicodeDecodeError: 无法解码README文件", self.file)
                name = self.file +'\n'
                with open("readme_error.txt", "a") as file:
                    file.write(name)
        
        self.metadata = metadata
        self.readme = readme

    def extract_info(self):
        error_flag = self.unzip()
        if error_flag:
            return self.author, self.description, self.dirnum, self.license, self.readme, self.projectURL, self.repository, error_flag
            
        self.get_content()
        metadata = self.metadata
        
        # author
        start_tag = '<authors>'
        end_tag = '</authors>'
        start_index = metadata.find(start_tag) + len(start_tag)
        end_index = metadata.find(end_tag)
        self.author += metadata[start_index:end_index]
        
        # description
        start_tag = '<description>'
        end_tag = '</description>'
        start_index = metadata.find(start_tag) + len(start_tag)
        end_index = metadata.find(end_tag)
        self.description += metadata[start_index:end_index]
        
        # projectURL
        start_tag = '<projectUrl>'
        end_tag = '</projectUrl>'
        start_index = metadata.find(start_tag) + len(start_tag)
        end_index = metadata.find(end_tag)
        if start_index == -1 or end_index == -1:
            self.projectURL = ""
        else:
            this_projectURL = metadata[start_index:end_index]
            try:
                domain = urlparse(this_projectURL).netloc
                self.projectURL = ".".join(domain.split('.')[-2:])
            except Exception as e:
                print(e)
                self.projectURL = ""
        
        
        # repository
        start_tag = '<repository'
        end_tag = '/>'
        start_index = metadata.find(start_tag) + len(start_tag)
        end_index = metadata.find(end_tag)
        string = metadata[start_index:end_index]
        url_pattern = re.compile(r'url="(.*?)"')
        urls = url_pattern.findall(string)
        for url in urls:
            self.repository += url
            self.repository += " "
        
        
        # licenseUrl
        license_tag = '<licenseUrl>'
        index = metadata.find(license_tag)
        # print(index)
        if index != -1:
            self.license = 1
            # print(license)
        return self.author, self.description, self.dirnum, self.license, self.readme, self.projectURL, self.repository, error_flag
        
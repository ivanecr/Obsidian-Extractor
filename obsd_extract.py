import re
import os
from sys import argv
from zipfile import ZipFile

class Parser:
    def __init__(self, folderPath='.', tag=None):
        self._folderPath = folderPath
        self._tag = tag
        self._regexFindLinks = '(?<=\[\[).*?(?=(?:\]\]|#|\|))' # Thanks to https://github.com/archelpeg
        self._regexFindTags = '#\S+'
        self._mdFiles = []
        self._called = False
        self._retrieveMarkdownFiles()
        self._currentFileAsHtml = None
        self._addedFiles = set()

    def _retrieveMarkdownFiles(self):
        """Directory traversal to find all .md files and stores them in _mdFiles

        Full credit goes to: https://github.com/archelpeg
        """
        if self._called: raise Exception('Files have already been retrieved')
        for dirpath, dirnames, files in os.walk(self._folderPath):
            # print(f'Found directory: {dirpath}')
            for file_name in files:
                if file_name.endswith('.md'):
                    #print(file_name)
                    # normalises path for current file system
                    normalised_path = os.path.normpath(dirpath + "/" + file_name)
                    self._mdFiles.append(normalised_path)
        self._called = True

    def _findFilesWithTag(self, tag=None):
        """Find all files containing a specific tag
        """
        for file in self._mdFiles:
            self._openFileAsString(file)
            if self._tagInCurrentFile(tag):
                self._addedFiles.add(file)


    def _tagInCurrentFile(self, tag):
        """Check if tag is in Current File
        """
        tags = set(re.findall(self._regexFindTags, self._currentFileAsHtml))
        tags = [tag[1:] for tag in tags]
        return tag in tags

    def _findLinksInCurrentFile(self):
        """Return all links in the Current File"""
        return re.findall(self._regexFindLinks, self._currentFileAsHtml)

    def _openFileAsString(self, fileName):
        """Open one file and store the content in _currentFileAsHtml"""
        with open(fileName, "r", encoding="utf-8") as input_file:
            self._currentFileAsHtml = input_file.read()

    def _exportInZip(self, files, path=None):
        """Export all files in zip, if path not specified, export to current location"""
        if len(files) == 0:
            print('No files found, exiting now'); return
        if path == None:
            path = '.'
            print('Exporting to current path...')
        else:
            print(f'Exporting to {path}...')
        zipObj = ZipFile(f'Exported_{self._tag}.zip', 'w')
        print('###### FILES FOUND ######')
        for file in files:
            print(file)
            fileName = file.rsplit(f'{self._folderPath}/', 1)[-1]
            zipObj.write(file, os.path.join('.',fileName)) # Not sure if it recreates subfolders
        zipObj.close()
        print('######################')
        print('Exported!')

    def _findSubFilesForAddedFiles(self):
        """Iteration to grow _addedFiles while i can"""
        while not self._grow():
            pass


    def _grow(self):
        """Add new files found following links in _addedFiles"""
        addedFiles = set()
        for file in self._addedFiles:
            self._openFileAsString(file)
            linkedFiles = self._findLinksInCurrentFile() # all links in file
            linkedFiles = [link+'.md' for link in linkedFiles] # Added .md at the end
            linkedFiles = [file # Get the full links
                for file in self._mdFiles
                for link in linkedFiles
                if link in file
            ]
            linkedFiles = set(linkedFiles) - self._addedFiles # Only keep not added files
            for link in linkedFiles:
                addedFiles.add(link)
        for file in addedFiles:
            self._addedFiles.add(file)
        return len(addedFiles) == 0

    def run(self, recursive=False):
        """Run the script

        * If recursive option, will find all linkedFiles in order to keep the clicks
        """
        self._findFilesWithTag(self._tag)
        if recursive:
            self._findSubFilesForAddedFiles()
        self._exportInZip(self._addedFiles)


if len(argv) not in [4,5]: raise Exception("Usage: python3 vault_folder --tag your_tag")
folder = argv[1]
tag = argv[3]

parser = Parser(folderPath=folder, tag=tag)
parser.run(recursive='-r' in argv)
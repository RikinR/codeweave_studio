#dummy implementation for now!
from state import StudioState

class CodeWriteTool:
    def read_file(self):
        """dont want to call rag just copy from codebase uplaod location to save time and processsing and api cost"""
        print("called read file function")
        return "dummy_file"
    
    def write_file(self,patch):
        print("called write file function with final patched : ")
        print(patch)
        return "successfully wrote into file"


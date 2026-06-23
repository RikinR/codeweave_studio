#dummy implementation for now!

class CodeWriteTool:
    def read_file(self):
        """dont want to call rag just copy from codebase uplaod location to save time and processsing and api cost"""
        print("called read file function")
        return "dummy_file"
    
    def write_file(self,content):
        print("called write file function with content : ")
        print(content)
        return "successfully wrote into file"


import os

#Gets all .SQD files in the directory and its subdirectories

def get_files(directory):
    files = []
    for root, dirs, file in os.walk(directory):
        for f in file:
            if f.endswith(".sqd"):
                files.append(os.path.join(root, f))
    return files

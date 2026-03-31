import os
import shutil
import kagglehub

# Target directory
target_dir = r"h:\mini project\vibe\ppt purpose"

# Download latest version
print("Downloading dataset from Kaggle...")
try:
    path = kagglehub.dataset_download("ziya07/college-student-management-dataset")
    print("Downloaded to Kaggle cache:", path)

    # Copy files to our target directory
    print(f"Copying files to {target_dir}...")
    for item in os.listdir(path):
        s = os.path.join(path, item)
        d = os.path.join(target_dir, item)
        if os.path.isdir(s):
            shutil.copytree(s, d, dirs_exist_ok=True)
        else:
            shutil.copy2(s, d)

    print("Dataset successfully moved to ppt purpose folder.")
except Exception as e:
    print(f"Error during download or copy: {e}")

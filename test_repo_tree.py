import os
import openpyxl

target_dir = r"I:\خالي أحمد جلال"

def get_repo_tree():
    tree = []
    # Root files
    root_files = []
    for it in os.listdir(target_dir):
        p = os.path.join(target_dir, it)
        if os.path.isfile(p) and not it.startswith("~$"):
            root_files.append({
                "name": it,
                "rel_path": it,
                "size_kb": round(os.path.getsize(p) / 1024, 1),
                "ext": os.path.splitext(it)[1].lower()
            })
    if root_files:
        tree.append({
            "folder_name": "الملفات الرئيسية",
            "rel_dir": "",
            "count": len(root_files),
            "files": root_files
        })
    
    # Subdirectories
    for d in sorted(os.listdir(target_dir)):
        p = os.path.join(target_dir, d)
        if os.path.isdir(p):
            sub_files = []
            for root, dirs, files in os.walk(p):
                for f in files:
                    if f.startswith("~$"):
                        continue
                    fp = os.path.join(root, f)
                    rel = os.path.relpath(fp, target_dir)
                    sub_files.append({
                        "name": f,
                        "rel_path": rel,
                        "size_kb": round(os.path.getsize(fp) / 1024, 1),
                        "ext": os.path.splitext(f)[1].lower()
                    })
            tree.append({
                "folder_name": d,
                "rel_dir": d,
                "count": len(sub_files),
                "files": sub_files
            })
    return tree

tree = get_repo_tree()
print(f"Total folders in tree: {len(tree)}")
for folder in tree[:6]:
    print(f"  Folder: {folder['folder_name']} ({folder['count']} files)")

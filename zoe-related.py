import os
import json
import shutil

def find_and_copy_zoe_json(base_dir):
    target_dir = os.path.join(base_dir, "zoe-related")
    os.makedirs(target_dir, exist_ok=True) # 创建zoe-related文件夹

    for root, _, files in os.walk(base_dir): # 遍历当前文件夹
        for filename in files:
            if filename.lower().endswith(".json"): # 找到所有json工作流文件
                file_path = os.path.join(root, filename) # 合成绝对路径

                try:
                    with open(file_path, "r", encoding="utf-8") as f:
                        data = json.load(f) # 加载读取json文件

                    # 转换为不区分大小写的键名访问
                    def get_case_insensitive(d, key): # 参数1:json文件，参数2:要访问的键
                        for k in d:
                            if k.lower() == key.lower(): # 转换为小写进行搜索
                                return d[k]
                        return None

                    section_196 = get_case_insensitive(data, "196") # 查找键值196
                    if isinstance(section_196, dict):  # 三部查询，直到找到preprocessor
                        inputs = get_case_insensitive(section_196, "inputs")
                        if isinstance(inputs, dict):
                            preprocessor = get_case_insensitive(inputs, "preprocessor")
                            if isinstance(preprocessor, str) and preprocessor.lower() == "zoe-depthmappreprocessor".lower():
                                shutil.copy2(file_path, target_dir)
                                print(f"✅ 发现并复制: {file_path}")
                except (json.JSONDecodeError, OSError) as e: # 异常抛出
                    print(f"⚠️ 跳过文件 {file_path}，错误: {e}")

    print("\n🎯 处理完成，所有匹配文件已复制到 'zoe-related' 文件夹。")

if __name__ == "__main__":
    find_and_copy_zoe_json(os.getcwd())

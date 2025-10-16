import os
import shutil

def find_unprocessed_workflows():
    """
    查找在 'workflow' 文件夹中但没有对应 '.json.csv' 日志的 '.json' 文件，
    并将它们复制到 'workflow_left' 文件夹中。
    """
    # 定义目录路径
    # 当前目录
    current_dir = '.'
    # JSON 工作流文件所在目录
    workflow_dir = os.path.join(current_dir, 'workflow')
    # 输出结果的目标目录
    output_dir = os.path.join(current_dir, 'workflow_left')

    # --- 步骤 1: 检查所需目录是否存在 ---
    if not os.path.isdir(workflow_dir):
        print(f"错误：找不到 'workflow' 子文件夹。请确保脚本在正确的目录下运行。")
        return

    # --- 步骤 2: 获取所有已生成的 CSV 日志所对应的 JSON 文件名 ---
    # CSV 文件名为 'workflow_name.json.csv'
    # 我们需要提取出 'workflow_name.json' 这部分作为已处理的标记
    try:
        # 使用集合（set）以获得更快的查找速度
        processed_files = {
            f.replace('.csv', '') # 直接去掉末尾的 .csv
            for f in os.listdir(current_dir)
            if f.endswith('.json.csv') and os.path.isfile(os.path.join(current_dir, f))
        }
        print(f"成功找到 {len(processed_files)} 个 CSV 日志文件。")
    except Exception as e:
        print(f"读取当前目录下的 CSV 文件时出错: {e}")
        return

    # --- 步骤 3: 找到未处理的 JSON 文件 ---
    unprocessed_json_files = []
    try:
        for filename in os.listdir(workflow_dir):
            if filename.endswith('.json'):
                # 检查这个完整的 JSON 文件名（例如 'workflow1.json'）
                # 是否在已处理的集合中
                if filename not in processed_files:
                    unprocessed_json_files.append(filename)
    except Exception as e:
        print(f"遍历 'workflow' 文件夹时出错: {e}")
        return

    # --- 步骤 4: 处理找到的文件 ---
    if not unprocessed_json_files:
        print("\n恭喜！所有 'workflow' 文件夹下的 JSON 文件都已处理，没有遗漏。")
        return

    print(f"\n找到了 {len(unprocessed_json_files)} 个未处理的 JSON 工作流文件。")

    # --- 步骤 5: 创建输出目录并复制文件 ---
    try:
        # 如果目标文件夹不存在，则创建它
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
            print(f"已创建输出文件夹: '{output_dir}'")

        print("\n开始将未处理的 JSON 文件复制到 'workflow_left' 文件夹...")
        for json_file in unprocessed_json_files:
            source_path = os.path.join(workflow_dir, json_file)
            destination_path = os.path.join(output_dir, json_file)
            shutil.copy2(source_path, destination_path) # copy2 会同时复制元数据
            print(f"  - 已复制: {json_file}")
            
        print(f"\n处理完成！总共有 {len(unprocessed_json_files)} 个文件被复制到了 '{output_dir}' 文件夹中。")

    except Exception as e:
        print(f"\n在创建目录或复制文件时发生错误: {e}")

if __name__ == "__main__":
    find_unprocessed_workflows()
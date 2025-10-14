import os
import shutil
def extract_json_files(root_dir='.',output_folder='json_workflow',handle_duplicate='rename'):
    # 创建输出文件夹
    output_path=os.path.join(root_dir,output_folder)
    os.makedirs(output_path,exist_ok=True)
    print("-"*60)
    print("📁 JSON文件提取工具")
    print("-"*60)
    print(f"根目录:{os.path.abspath(root_dir)}")
    print(f"输出目录:{os.path.abspath(output_path)}")
    print(f"重名处理:{handle_duplicate}\n")

    # 统计信息
    total_found=0 # 总共找到多少json文件
    total_copied=0 # 总复制
    total_skipped=0 # 总共跳过多少文件
    duplicate_count=0 # 重名处理数量

    # 用于追踪已复制的文件名
    copied_files={}

    # 遍历所有文件
    for root,dirs,files in os.walk(root_dir):
        # 跳过输出文件夹本身
        if os.path.abspath(root)==os.path.abspath(output_path):
            continue

        # 过滤JSON文件
        json_files=[f for f in files if f.lower().endswith('.json') and not f.startswith('.')]

        for filename in json_files:
            total_found+=1
            source_path=os.path.join(root,filename)

            # 相对路径
            rel_path=os.path.relpath(source_path,root_dir)

            # 目标文件路径
            dest_path=os.path.join(output_path,filename)

            # 处理重名文件
            if os.path.exists(dest_path):
                if handle_duplicate=='skip':
                    print(f"➡️ 跳过(已存在):{rel_path}")
                    total_skipped+=1
                    continue
                elif handle_duplicate=='rename':
                    # 生成新文件名
                    name,ext=os.path.splitext(filename)
                    counter=1
                    new_filename=f"{name}_{counter}{ext}"
                    dest_path=os.path.join(output_path,new_filename)
                    while os.path.exists(dest_path):
                        counter+=1
                        new_filename=f"{name}_{counter}{ext}"
                        dest_path=os.path.join(output_path,new_filename)
                    print(f"♻️ 重命名:{rel_path}->{new_filename}")
                    duplicate_count+=1
                elif handle_duplicate=='overwrite':
                    print(f"♻️ 覆盖:{rel_path}")
                
            else:
                print(f"♻️ 复制:{rel_path}")
            
            # 复制文件
            try:
                shutil.copy2(source_path,dest_path)
                total_coped+=1

                # 记录已经复制的文件（统计用）
                final_filename=os.path.basename(dest_path)
                if final_filename not in copied_files:
                    copied_files[final_filename]=[]
                copied_files[final_filename].append(rel_path)
            except Exception as e:
                print(f"❌ 复制失败:{rel_path}-{e}")

    # 输出统计信息
    print('\n'+'-'*60)
    print(f"📈 提取完成统计")
    print('-'*60)
    print(f"发现文件:{total_found}")
    print(f"成功复制:{total_copied}")
    print(f"跳过文件:{total_skipped}")
    print(f"重命名文件:{duplicate_count}")
    print(f"\n✅ 所有文件已经保存到:{os.path.abspath(output_path)}")

    # 显示重命名文件的来源
    if duplicate_count>0 and handle_duplicate=='rename':
        print("\n"+"-"*60)
        print("⚠️ 重名文件来源")
        print("-"*60)
        for filename,sources in copied_files.items():
            if len(sources)>1:
                print(f"\n{filename}:")
                for idx,source in enumerate(sources,1):
                    print(f"{idx}.{source}")
                    
if __name__=='__main__':
    extract_json_files()
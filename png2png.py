from urllib import parse
import json 
import requests
import urllib
import time
import traceback
import csv
import random 
import os
import shutil

url = "www.comfyweb.com" # 此处填写comfyui线上环境的网址
image_exts = ('.png', '.jpg', '.jpeg', '.bmp', '.webp')

# ============ 通用重试方法 ============

def request_with_retry(method, url, max_retries=3, delay=3, timeout=10, **kwargs):
    '''
    一种增加网络请求健壮性的设计，为所有的http请求增加了自动重试机制
    '''
    for attempt in range(max_retries):
        try:
            response = requests.request(method, url, timeout=timeout, **kwargs)
            response.raise_for_status()
            return response
        except Exception as e:
            print(f"[{method.upper()}] Attempt {attempt + 1}/{max_retries} failed: {e}")
            if attempt < max_retries - 1:
                time.sleep(delay)
            else:
                raise

# ============ 网络相关函数 ============

def download_image(prefix, urls, save_path):
    '''
    作用：从服务器下载处理好的图片
    '''
    count = 0
    for url_tail in urls:
        url_tail = prefix + url_tail
        try:
            response = request_with_retry("GET", url_tail)
            save_path_new = save_path.replace(".png", "_" + str(count) + ".png")
            with open(save_path_new, 'wb') as file:
                file.write(response.content)
            count += 1
        except Exception as e:
            print(f"Download failed: {e}")
    return

def get_image(filename, subfolder, folder_type):
    '''
    生成一个用于查看或下载图片的URL查询字符串
    '''
    data = {"filename": filename, "subfolder": subfolder, "type": folder_type}
    url_values = urllib.parse.urlencode(data)
    return url_values

def upload_file(file, subfolder="", overwrite=False):
    '''
    上传本地图片到ComfyUI服务器
    '''
    path = ""
    try:
        body = {"image": file}
        data = {}

        if overwrite:
            data["overwrite"] = "true"
        if subfolder:
            data["subfolder"] = subfolder

        resp = request_with_retry("POST", url + "/upload/image", files=body, data=data)
        if resp.status_code == 200:
            data = resp.json()
            path = data["name"]
            if "subfolder" in data and data["subfolder"] != "": 
                path = data["subfolder"] + "/" + path
        else:
            print(f"{resp.status_code} - {resp.reason}")
    except Exception as error:
        print(f"Upload error: {error}")
    return path

def queue_prompt(pid):
    '''
    轮流查询服务器，检查一个任务是否已经完成
    若返回数据包含含pid的结果，说明任务成功了
    '''
    print("wait", time.time())
    while True:
        try:
            response_new = request_with_retry("GET", url + "/history/" + pid)
            if response_new and len(response_new.json()) > 0:
                out_urls = []
                for node_id in response_new.json()[pid]['outputs']:
                    node_output = response_new.json()[pid]['outputs'][node_id]
                    if 'images' in node_output:
                        for image in node_output['images']:
                            url_values = get_image(image['filename'], image['subfolder'], image['type'])
                            out_urls.append(url_values)
                print("generate", time.time())
                return out_urls
        except Exception as e:
            print(f"Polling error, retrying in 3s: {e}")
            time.sleep(3)

def find_image_input_node(workflow):
    """
    查找工作流中的图片输入节点
    
    返回:
        str: 节点ID（如果找到）
        None: 如果没有找到（表示这是文生图工作流）
    """
    for node_id, node in workflow.items():
        if isinstance(node, dict) and ("class_type" in node or "type" in node):
            if "LoadImageFromUrlOrPath" in node.get("class_type", "") or "LoadImage" in node.get("class_type", ""):
                return node_id
    return None  # 没有找到图片输入节点

def push_prompt(prompt):
    p = {"prompt": prompt}
    data = json.dumps(p).encode('utf-8')
    response = request_with_retry("POST", url + '/prompt', data=data)
    print(response.json())
    prompt_id = response.json()['prompt_id']
    return prompt_id

# ============ 保存错误工作流函数 ============

def save_error_workflow(workflow_path, error_folder="error_workflow"):
    """
    将出错的工作流文件复制到错误文件夹
    
    参数:
        workflow_path: 工作流文件的完整路径
        error_folder: 错误文件夹名称（默认 error_workflow）
    """
    try:
        os.makedirs(error_folder, exist_ok=True)
        filename = os.path.basename(workflow_path)
        dest_path = os.path.join(error_folder, filename)
        shutil.copy2(workflow_path, dest_path)
        print(f"📁 已保存错误工作流到: {dest_path}")
    except Exception as e:
        print(f"⚠️  保存错误工作流失败: {e}")

# ============ 新增：处理文生图工作流 ============

def process_text_to_image_workflow(workflow, write_folder, log_file, workflow_name):
    """
    处理文生图工作流（不需要输入图片）
    
    返回:
        tuple: (是否成功, 错误信息)
    """
    try:
        print("📝 检测到文生图工作流，直接生成图片...")
        
        start = time.time()
        out_path = os.path.abspath(
            os.path.join(write_folder, f"{workflow_name}_output.png")
        )
        
        # 执行任务
        total_start = time.time()
        submit_start = time.time()
        prompt_id = push_prompt(workflow)
        submit_end = time.time()
        
        generate_start = time.time()
        url_values = queue_prompt(prompt_id)
        generate_end = time.time()
        
        download_start = time.time()
        download_image(url + "/view?", url_values, out_path)
        download_end = time.time()
        total_end = time.time()
        
        print(f"⏱️  Total time for text-to-image: {total_end - total_start:.2f}s")
        
        # 记录成功日志
        with open(log_file, 'a', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow([
                "0001",
                "N/A (text-to-image)",
                out_path,
                f"{submit_end - submit_start:.2f}",
                f"{generate_end - generate_start:.2f}",
                f"{download_end - download_start:.2f}",
                f"{total_end - total_start:.2f}",
                "success",
                ""
            ])
        
        return True, ""
        
    except Exception as e:
        err_msg = traceback.format_exc()
        print(f"❌ 文生图处理失败: {e}")
        
        # 记录失败日志
        with open(log_file, 'a', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow([
                "0001",
                "N/A (text-to-image)",
                out_path if 'out_path' in locals() else "N/A",
                "", "", "", "",
                "fail",
                err_msg.replace("\n", " | ")
            ])
        
        return False, str(e)

# ============ 新增：处理图生图工作流 ============

def process_image_to_image_workflow(workflow, image_node_id, read_folder, write_folder, log_file):
    """
    处理图生图工作流（需要输入图片）
    
    返回:
        tuple: (是否有错误, 错误信息, 处理数量)
    """
    count = 0
    has_error = False
    error_msg = ""
    
    for roots, dirs, files in os.walk(read_folder):
        image_files = [f for f in files if f.lower().endswith(image_exts) and not f.startswith('.')]
        if not image_files:
            continue
            
        for p in image_files:
            if not p.startswith('.'):
                path = os.path.join(roots, p)
                
                try:
                    # 上传图片
                    with open(path, 'rb') as f:
                        comfyui_path_image = upload_file(f, "", True)
                    print(f"📤 上传: {comfyui_path_image}")
                    
                    # 修改工作流
                    workflow[image_node_id]["inputs"]['image'] = comfyui_path_image
                    
                    start = time.time()
                    out_path = os.path.abspath(
                        os.path.join(write_folder, p.strip())
                    )
                    
                    # 执行任务
                    total_start = time.time()
                    submit_start = time.time()
                    prompt_id = push_prompt(workflow)
                    submit_end = time.time()
                    
                    generate_start = time.time()
                    url_values = queue_prompt(prompt_id)
                    generate_end = time.time()
                    
                    download_start = time.time()
                    download_image(url + "/view?", url_values, out_path)
                    download_end = time.time()
                    total_end = time.time()
                    
                    print(f"⏱️  Total time for image {count + 1}: {total_end - total_start:.2f}s")
                    
                    # 记录成功日志
                    with open(log_file, 'a', newline='', encoding='utf-8') as csvfile:
                        writer = csv.writer(csvfile)
                        writer.writerow([
                            f"{count + 1:04d}",
                            path,
                            out_path,
                            f"{submit_end - submit_start:.2f}",
                            f"{generate_end - generate_start:.2f}",
                            f"{download_end - download_start:.2f}",
                            f"{total_end - total_start:.2f}",
                            "success",
                            ""
                        ])
                        
                except Exception as e:
                    err_msg = traceback.format_exc()
                    print(f"❌ Error processing image {count + 1}: {e}")
                    
                    has_error = True
                    error_msg = str(e)
                    
                    # 记录失败日志
                    with open(log_file, 'a', newline='', encoding='utf-8') as csvfile:
                        writer = csv.writer(csvfile)
                        writer.writerow([
                            f"{count + 1:04d}",
                            path,
                            out_path if 'out_path' in locals() else "N/A",
                            "", "", "", "",
                            "fail",
                            err_msg.replace("\n", " | ")
                        ])
                
                count += 1
                end = time.time()
                print(f"⏱  diff {end - start:.2f}s")
    
    return has_error, error_msg, count

# ============ 主程序入口 ============

if __name__ == '__main__':
    input_folder = '/Users/xxx/xxx/xxx/workflow' # 此处填写工作流文件夹
    read_folder = "/Users/xxx/xxx/xxx/pic"  # 此处填写图生图时读取图片的文件夹
    
    error_workflow_folder = "error_workflow"
    os.makedirs(error_workflow_folder, exist_ok=True)
    
    error_log_file = "error_workflows.csv"
    if not os.path.exists(error_log_file):
        with open(error_log_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['工作流文件名', '错误时间', '工作流类型', '处理阶段', '错误信息'])
    
    # 获取所有 JSON 文件并排序
    json_files = sorted([f for f in os.listdir(input_folder) 
                        if f.endswith('.json') and not f.startswith('.')])
    
    print(f"📊 发现 {len(json_files)} 个工作流文件")
    print(f"文件列表: {json_files}\n")
    
    processed_count = 0
    error_count = 0
    text_to_image_count = 0
    image_to_image_count = 0
    
    for pro in json_files:
        workflow_path = os.path.join(input_folder, pro)
        workflow_has_error = False
        workflow_error_msg = ""
        error_stage = ""
        workflow_type = "未知"
        
        try:
            print(f"\n{'='*60}")
            print(f"🔄 Processing workflow [{processed_count + 1}/{len(json_files)}]: {pro}")
            print(f"{'='*60}")
            
            # ============ 阶段1: 读取工作流 ============
            try:
                with open(workflow_path, "r", encoding="utf-8") as f:
                    workflow_data = f.read()
                workflow = json.loads(workflow_data)
                print("✅ 工作流读取成功")
            except Exception as e:
                error_stage = "文件读取/解析"
                raise Exception(f"工作流文件读取失败: {e}")
            
            # ============ 阶段2: 准备输出目录 ============
            write_folder_name = os.path.splitext(pro)[0]
            write_folder = os.path.join("out", f"{write_folder_name}")
            os.makedirs(write_folder, exist_ok=True)
            
            log_file = f"{pro}.csv"
            
            # ============ 阶段3: 判断工作流类型 ============
            image_node_id = find_image_input_node(workflow)
            
            if image_node_id is None:
                # 文生图工作流
                workflow_type = "文生图"
                print(f"🎨 检测到 [{workflow_type}] 工作流")
                text_to_image_count += 1
                
                error_stage = "文生图处理"
                success, err_msg = process_text_to_image_workflow(
                    workflow, write_folder, log_file, write_folder_name
                )
                
                if not success:
                    workflow_has_error = True
                    workflow_error_msg = err_msg
                
            else:
                # 图生图工作流
                workflow_type = "图生图"
                print(f"🖼️  检测到 [{workflow_type}] 工作流")
                print(f"✅ 找到图片输入节点: {image_node_id}")
                image_to_image_count += 1
                
                error_stage = "图生图处理"
                has_error, err_msg, count = process_image_to_image_workflow(
                    workflow, image_node_id, read_folder, write_folder, log_file
                )
                
                if has_error:
                    workflow_has_error = True
                    workflow_error_msg = err_msg
                
                print(f"✅ 工作流 {pro} 处理完成 (处理了 {count} 张图片)")
            
            # 工作流处理完成
            processed_count += 1
            
            # 如果有错误，保存到错误文件夹
            if workflow_has_error:
                save_error_workflow(workflow_path, error_workflow_folder)
                error_count += 1
                
                with open(error_log_file, 'a', newline='', encoding='utf-8') as f:
                    writer = csv.writer(f)
                    writer.writerow([
                        pro,
                        time.strftime('%Y-%m-%d %H:%M:%S'),
                        workflow_type,
                        error_stage,
                        workflow_error_msg
                    ])
        
        except Exception as e:
            # 工作流级别的致命错误
            print(f"\n❌ 工作流 {pro} 处理失败: {e}")
            print(traceback.format_exc())
            
            error_count += 1
            
            # 保存到错误文件夹
            try:
                save_error_workflow(workflow_path, error_workflow_folder)
            except:
                pass
            
            # 记录到错误日志
            with open(error_log_file, 'a', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow([
                    pro,
                    time.strftime('%Y-%m-%d %H:%M:%S'),
                    workflow_type,
                    error_stage if error_stage else "工作流初始化",
                    str(e)
                ])
            
            print(f"⏭️  跳过该工作流，继续处理下一个...\n")
            continue
    
    # ============ 最终统计 ============
    print(f"\n{'='*60}")
    print(f"📊 处理完成统计")
    print(f"{'='*60}")
    print(f"总文件数: {len(json_files)}")
    print(f"成功处理: {processed_count}")
    print(f"  - 文生图: {text_to_image_count}")
    print(f"  - 图生图: {image_to_image_count}")
    print(f"失败数量: {error_count}")
    print(f"未处理数: {len(json_files) - processed_count}")
    
    if error_count > 0:
        print(f"\n⚠️  {error_count} 个工作流处理失败，已保存到 {error_workflow_folder}/")
        print(f"详细错误信息请查看: {error_log_file}")
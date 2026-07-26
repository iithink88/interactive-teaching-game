import json
import os
import sys
import base64
from io import BytesIO

def find_matching_image(desired_path, json_dir, images_dir="images"):
    """
    智能查找图片文件，支持模糊匹配
    当精确匹配失败时，尝试查找同名的不同扩展名文件
    """
    # 先尝试精确匹配
    exact_path = os.path.join(json_dir, desired_path)
    if os.path.exists(exact_path):
        return exact_path
    
    # 解析期望的文件名（不含扩展名和路径）
    # 例如: images/cover.jpg → cover
    filename = os.path.basename(desired_path)  # cover.jpg
    name_without_ext = os.path.splitext(filename)[0]  # cover
    
    # 检查 images/ 目录是否存在
    images_path = os.path.join(json_dir, images_dir)
    if not os.path.exists(images_path):
        return None
    
    # 扫描目录找同名文件（不同扩展名）
    supported_extensions = ['.jpg', '.jpeg', '.png', '.webp', '.gif']
    for file in os.listdir(images_path):
        file_name_without_ext = os.path.splitext(file)[0]
        file_ext = os.path.splitext(file)[1].lower()
        
        if file_name_without_ext == name_without_ext and file_ext in supported_extensions:
            matched_path = os.path.join(images_path, file)
            print(f"    智能匹配: {desired_path} → {file}")
            return matched_path
    
    return None

def compress_image(image_data, max_width=1920, quality=85, format='JPEG'):
    """
    Compress image using Pillow if available, otherwise return original.
    Falls back to original if Pillow not installed.
    """
    try:
        from PIL import Image
        # Open image from bytes
        img = Image.open(BytesIO(image_data))
        
        # Check if needs compression
        original_size_mb = len(image_data) / (1024 * 1024)
        original_width = img.width
        
        # Skip compression if already small enough
        if original_width <= max_width and original_size_mb < 1:
            print(f"    图片已优化: {original_width}x{img.height}, {original_size_mb:.2f}MB (无需压缩)")
            return base64.b64encode(image_data).decode('utf-8')
        
        # Resize if needed
        if img.width > max_width:
            ratio = max_width / img.width
            new_height = int(img.height * ratio)
            img = img.resize((max_width, new_height), Image.LANCZOS)
            print(f"    图片已缩放: {original_width}x{img.height} → {max_width}x{new_height}")
        
        # Convert to RGB if necessary (for JPEG)
        if format == 'JPEG' and img.mode in ('RGBA', 'P'):
            img = img.convert('RGB')
        
        # Compress
        output = BytesIO()
        img.save(output, format=format, quality=quality, optimize=True)
        compressed_data = output.getvalue()
        
        compressed_size_mb = len(compressed_data) / (1024 * 1024)
        compression_ratio = (1 - len(compressed_data) / len(image_data)) * 100
        
        print(f"    压缩完成: {compressed_size_mb:.2f}MB (节省 {compression_ratio:.1f}%)")
        return base64.b64encode(compressed_data).decode('utf-8')
        
    except ImportError:
        print("    警告: 未安装 Pillow 库，跳过图片压缩")
        print("    安装方法: pip install Pillow")
        return base64.b64encode(image_data).decode('utf-8')
    except Exception as e:
        print(f"    警告: 图片压缩失败: {e}")
        return base64.b64encode(image_data).decode('utf-8')

def resolve_image_path(image_path, json_dir):
    """
    Resolve the image path. Returns absolute path if found, None if not.
    Supports relative paths relative to JSON file directory.
    """
    if not image_path:
        return None
    
    # Already base64 or URL
    if image_path.startswith("data:") or image_path.startswith("http"):
        return image_path
    
    # Try absolute path
    if os.path.isabs(image_path) and os.path.exists(image_path):
        return image_path
    
    # Try relative to JSON file directory
    relative_path = os.path.join(json_dir, image_path)
    if os.path.exists(relative_path):
        return relative_path
    
    # Try intelligent matching (same name, different extension)
    matched_path = find_matching_image(image_path, json_dir)
    if matched_path and os.path.exists(matched_path):
        return matched_path
    
    # Try relative to current working directory
    if os.path.exists(image_path):
        return image_path
    
    return None

def load_image_as_base64(image_path, json_dir, max_size_mb=5):
    """
    Load an image from path and return base64 string.
    Supports png, jpg, jpeg, webp.
    Compresses images to limit file size.
    Raises exception if image not found or too large.
    Includes detailed error reporting with available files.
    """
    resolved_path = resolve_image_path(image_path, json_dir)
    
    if not resolved_path or not os.path.exists(resolved_path):
        # Generate detailed error with available files
        images_dir = os.path.join(json_dir, "images")
        available_files = []
        if os.path.exists(images_dir):
            available_files = [f for f in os.listdir(images_dir) 
                             if os.path.splitext(f)[1].lower() in ['.jpg', '.jpeg', '.png', '.webp', '.gif']]
        
        error_msg = f"图片未找到: {image_path}\n"
        error_msg += f"已尝试的路径:\n"
        error_msg += f"  - 绝对路径: {os.path.abspath(image_path)}\n"
        error_msg += f"  - 相对JSON目录: {os.path.join(json_dir, image_path)}\n"
        error_msg += f"  - 智能匹配: 已尝试查找同名不同扩展名的文件\n"
        
        if available_files:
            error_msg += f"\n可用的图片文件 (在 images/ 目录下):\n"
            for f in available_files:
                error_msg += f"  - images/{f}\n"
            error_msg += f"\n提示: 确认文件名是否匹配，如 'cover.jpg' 对应 'images/cover.jpg'"
        else:
            error_msg += f"\n警告: images/ 目录不存在或为空"
        
        error_msg += f"\n解决方法:\n"
        error_msg += f"  1. 确保图片保存在 user-data/images/ 目录下\n"
        error_msg += f"  2. 检查 game_config.json 中的路径格式应为 'images/xxx.jpg'\n"
        error_msg += f"  3. 确认图片文件名是否正确（支持 jpg, png, webp 格式）"
        
        raise FileNotFoundError(error_msg)
    
    ext = os.path.splitext(resolved_path)[1].lower().replace('.', '')
    if ext == 'jpg': 
        ext = 'jpeg'
    elif ext not in ['png', 'jpeg', 'webp', 'gif']:
        raise ValueError(f"不支持的图片格式: {ext}。仅支持 png, jpg, jpeg, webp")
    
    try:
        with open(resolved_path, "rb") as image_file:
            image_data = image_file.read()
            file_size_mb = len(image_data) / (1024 * 1024)
            
            # Warn if too large
            if file_size_mb > max_size_mb:
                print(f"    警告: 图片 {os.path.basename(image_path)} 较大 ({file_size_mb:.2f}MB)")
                print(f"    建议压缩到 {max_size_mb}MB 以下以优化加载速度")
            
            # Compress image
            compressed_base64 = compress_image(image_data, max_width=1920, quality=85, format='JPEG' if ext in ['jpg', 'jpeg'] else 'PNG')
            return f"data:image/{ext};base64,{compressed_base64}"
            
    except Exception as e:
        raise IOError(f"图片读取失败 {resolved_path}: {e}")

def build_game(json_path, template_path, output_path):
    json_dir = os.path.dirname(os.path.abspath(json_path))
    
    print("=" * 60)
    print("语文互动教学游戏构建工具")
    print("=" * 60)
    print(f"配置文件: {json_path}")
    print(f"模板文件: {template_path}")
    print(f"输出文件: {output_path}")
    print("=" * 60)
    
    # 1. Load Game Data
    print("\n[步骤 1/5] 加载游戏配置...")
    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            game_data = json.load(f)
        print("✓ 配置文件加载成功")
    except FileNotFoundError:
        raise FileNotFoundError(f"配置文件未找到: {json_path}")
    except json.JSONDecodeError as e:
        raise ValueError(f"配置文件格式错误: {e}")
    except Exception as e:
        raise Exception(f"加载配置文件失败: {e}")

    # 2. Validate Game Data Structure
    print("\n[步骤 2/5] 验证数据结构...")
    required_fields = ["title", "intro", "start_scene_id", "scenes", "review"]
    for field in required_fields:
        if field not in game_data:
            raise ValueError(f"配置文件缺少必要字段: {field}")
    
    # Validate each scene has unique image and exactly 3 choices (1 correct, 2 wrong)
    scene_images = {}
    for idx, scene in enumerate(game_data.get("scenes", [])):
        scene_id = scene.get("id", f"场景{idx+1}")
        
        # Check image field exists and is unique
        if "image" not in scene or not scene["image"]:
            raise ValueError(f"场景 [{scene_id}] 缺少 image 字段，每个场景必须指定独立的图片路径")
        
        img_path = scene["image"]
        if img_path in scene_images:
            raise ValueError(
                f"场景图片重复: 场景 [{scene_id}] 和场景 [{scene_images[img_path]}] 使用了相同的图片 '{img_path}'\n"
                f"每个场景必须有独立的图片"
            )
        scene_images[img_path] = scene_id
        
        # Check choices: exactly 3, with 1 correct and 2 wrong
        choices = scene.get("choices", [])
        if len(choices) != 3:
            raise ValueError(f"场景 [{scene_id}] 选项数量错误: 期望 3 个，实际 {len(choices)} 个")
        
        correct_count = sum(1 for c in choices if c.get("is_correct", False))
        if correct_count != 1:
            raise ValueError(f"场景 [{scene_id}] 正确选项数量错误: 期望 1 个，实际 {correct_count} 个")
    
    print("✓ 数据结构验证通过")

    # 3. Process Images (Convert to Base64)
    print("\n[步骤 3/5] 处理图片并转换为 Base64...")
    images_processed = 0
    images_failed = []
    
    # Process Cover Image for Start Screen
    if "cover_image" in game_data and game_data["cover_image"]:
        try:
            print(f"  处理封面图: {game_data['cover_image']}")
            base64_img = load_image_as_base64(game_data["cover_image"], json_dir)
            game_data["cover_image"] = base64_img
            images_processed += 1
            print(f"  ✓ 封面图处理成功")
        except Exception as e:
            images_failed.append(("封面图", str(e)))
            raise e
    
    # Process Scene Images
    if "scenes" in game_data:
        for idx, scene in enumerate(game_data["scenes"]):
            if "image" in scene and scene["image"]:
                scene_id = scene.get("id", f"场景{idx+1}")
                try:
                    print(f"  处理场景图 [{scene_id}]: {scene['image']}")
                    base64_img = load_image_as_base64(scene["image"], json_dir)
                    scene["image"] = base64_img
                    images_processed += 1
                    print(f"  ✓ 场景图 [{scene_id}] 处理成功")
                except Exception as e:
                    images_failed.append((scene_id, str(e)))
                    raise e
    
    print(f"\n✓ 图片处理完成，共处理 {images_processed} 张图片")

    # 4. Load Template
    print("\n[步骤 4/5] 加载模板...")
    try:
        with open(template_path, 'r', encoding='utf-8') as f:
            template_content = f.read()
        print("✓ 模板加载成功")
    except FileNotFoundError:
        raise FileNotFoundError(f"模板文件未找到: {template_path}")
    except Exception as e:
        raise Exception(f"加载模板失败: {e}")

    # 5. Inject Data and Write Output
    print("\n[步骤 5/5] 生成最终 HTML 文件...")
    json_str = json.dumps(game_data, ensure_ascii=False)
    title = game_data.get("title", "Interactive Game")
    
    output_content = template_content.replace("{{ title }}", title)
    output_content = output_content.replace("{{ game_data }}", json_str)

    try:
        output_dir = os.path.dirname(output_path)
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir)
            
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(output_content)
        
        file_size = os.path.getsize(output_path)
        file_size_mb = file_size / (1024 * 1024)
        print(f"✓ 游戏文件生成成功")
        print(f"  文件路径: {os.path.abspath(output_path)}")
        print(f"  文件大小: {file_size_mb:.2f} MB")
    except Exception as e:
        raise Exception(f"写入输出文件失败: {e}")
    
    print("\n" + "=" * 60)
    print("构建完成！")
    print("=" * 60)

if __name__ == "__main__":
    if len(sys.argv) < 4:
        print("用法: python build_game.py <json_config_path> <template_path> <output_html_path>")
        print("\n示例:")
        print("  python build_game.py user-data/game_config.json assets/template.html user-data/output_game.html")
        sys.exit(1)
    
    json_path = sys.argv[1]
    template_path = sys.argv[2]
    output_path = sys.argv[3]
    
    try:
        build_game(json_path, template_path, output_path)
    except Exception as e:
        print("\n" + "=" * 60)
        print("错误: 构建失败")
        print("=" * 60)
        print(f"错误详情: {e}")
        print("\n请检查以下内容:")
        print("  1. game_config.json 是否存在且格式正确")
        print("  2. 图片文件是否保存在 user-data/images/ 目录下")
        print("  3. JSON 中的图片路径是否为 'images/xxx.jpg' 格式")
        print("  4. 模板文件 assets/template.html 是否存在")
        sys.exit(1)

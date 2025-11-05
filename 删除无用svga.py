import os
import re
import sys
import shutil

# 定义项目根目录
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
# 定义assets目录路径
ASSETS_DIR = os.path.join(PROJECT_ROOT, 'app', 'src', 'main', 'assets')
# 定义要搜索的代码文件扩展名
CODE_EXTENSIONS = ['.java', '.kt', '.xml']
# 定义要搜索的svga文件扩展名
SVGA_EXTENSION = '.svga'

# 存储所有被引用的svga文件路径
referenced_svga_files = set()
# 存储所有实际存在的svga文件路径
all_svga_files = []


def search_referenced_svga():
    """搜索所有代码文件中引用的svga文件"""
    print("开始搜索代码中引用的svga文件...")
    
    # 遍历项目中的所有代码文件
    for root, dirs, files in os.walk(PROJECT_ROOT):
        # 排除一些不需要搜索的目录
        if '.git' in dirs: 
            dirs.remove('.git')
        if 'build' in dirs:
            dirs.remove('build')
        if '.gradle' in dirs:
            dirs.remove('.gradle')
        if '.idea' in dirs:
            dirs.remove('.idea')
        
        for file in files:
            # 检查文件扩展名
            _, ext = os.path.splitext(file)
            if ext not in CODE_EXTENSIONS:
                continue
            
            file_path = os.path.join(root, file)
            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                    
                    # 搜索svga文件引用
                    # 匹配类似: raxidor_svga_files/raxidor_cp/raxidor_ring_flash.svga
                    matches = re.findall(r'["\']([^"\']+\.svga)["\']', content)
                    for match in matches:
                        # 处理可能的相对路径
                        if not os.path.isabs(match):
                            # 计算相对于assets目录的路径
                            svga_path = os.path.normpath(os.path.join(ASSETS_DIR, match))
                            if os.path.exists(svga_path):
                                referenced_svga_files.add(svga_path)
                            else:
                                # 检查assets下的子目录
                                for root_assets, _, files_assets in os.walk(ASSETS_DIR):
                                    for file_assets in files_assets:
                                        if file_assets == match or match.endswith('/' + file_assets):
                                            full_path = os.path.normpath(os.path.join(root_assets, file_assets))
                                            referenced_svga_files.add(full_path)
                                            break
            except Exception as e:
                print(f"读取文件失败: {file_path}, 错误: {e}")
    
    print(f"找到 {len(referenced_svga_files)} 个被引用的svga文件")


def find_all_svga_files():
    """找到所有实际存在的svga文件"""
    print("开始查找所有实际存在的svga文件...")
    
    for root, _, files in os.walk(ASSETS_DIR):
        for file in files:
            if file.endswith(SVGA_EXTENSION):
                full_path = os.path.normpath(os.path.join(root, file))
                all_svga_files.append(full_path)
    
    print(f"找到 {len(all_svga_files)} 个实际存在的svga文件")


def remove_unused_svga(backup_dir=None):
    """移除未被引用的svga文件"""
    # 如果提供了备份目录，创建它
    if backup_dir:
        os.makedirs(backup_dir, exist_ok=True)
        print(f"将创建备份到: {backup_dir}")
    
    # 计算未被引用的svga文件
    unused_svga_files = [f for f in all_svga_files if f not in referenced_svga_files]
    
    print(f"找到 {len(unused_svga_files)} 个未被引用的svga文件")
    
    # 移除或备份未被引用的svga文件
    for svga_file in unused_svga_files:
        print(f"处理未引用文件: {svga_file}")
        
        if backup_dir:
            # 计算备份路径
            rel_path = os.path.relpath(svga_file, ASSETS_DIR)
            backup_path = os.path.join(backup_dir, rel_path)
            # 创建必要的目录
            os.makedirs(os.path.dirname(backup_path), exist_ok=True)
            # 移动文件到备份目录
            shutil.move(svga_file, backup_path)
            print(f"  已备份到: {backup_path}")
        else:
            # 直接删除文件
            os.remove(svga_file)
            print(f"  已删除")
    
    return len(unused_svga_files)


def main():
    """主函数"""
    # 搜索被引用的svga文件
    search_referenced_svga()
    
    # 查找所有实际存在的svga文件
    find_all_svga_files()
    
    # 询问用户是否要移除未被引用的svga文件
    print("\n准备移除未被引用的svga文件")
    print("注意: 此操作可能会影响项目功能，请确保备份重要数据！")
    
    # 询问是否创建备份
    create_backup = input("是否创建备份？(y/n): ").lower() == 'y'
    backup_dir = None
    if create_backup:
        backup_dir = input("请输入备份目录路径 (默认为 project_root/unused_svga_backup): ")
        if not backup_dir:
            backup_dir = os.path.join(PROJECT_ROOT, 'unused_svga_backup')
    
    # 确认删除
    confirm = input("确认移除未被引用的svga文件？(y/n): ").lower()
    if confirm == 'y':
        # 移除未被引用的svga文件
        removed_count = remove_unused_svga(backup_dir)
        print(f"\n操作完成！已处理 {removed_count} 个未被引用的svga文件")
    else:
        print("操作已取消")


if __name__ == "__main__":
    main()

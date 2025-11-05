import sys
import tkinter as tk
import subprocess  # 导入subprocess模块用于执行系统指令
import os  # {{导入os模块处理文件路径 }}
import json  # {{导入json模块处理配置文件 }}
import threading  # {{导入线程模块 }}
from tkinter import scrolledtext, ttk, filedialog

global bundletoolName
bundletoolName = "bundletool-all-1.18.2.jar"


# 获取程序运行路径（兼容打包后环境）
def get_resource_path(relative_path):
    """获取资源文件的绝对路径（支持PyInstaller打包后环境）"""
    # if hasattr(sys, '_MEIPASS'):
    #     # 打包后环境，资源文件会被提取到临时目录
    #     return os.path.join(sys._MEIPASS, relative_path)
    # 开发环境，直接使用相对路径
    return os.path.join(os.path.abspath('.'), relative_path)


# {{打开输出文件夹函数 }}
def open_output_folder():
    """打开APK输出目录（AAB文件所在目录）"""
    aab_path = file_path_var.get()
    if not aab_path:
        output_text.delete(1.0, tk.END)
        output_text.insert(tk.END, "错误：请先选择AAB文件", "red")
        return

    # 获取AAB文件所在目录（即APK输出目录）
    output_dir = os.path.dirname(aab_path)
    if not os.path.exists(output_dir):
        output_text.delete(1.0, tk.END)
        output_text.insert(tk.END, f"错误：输出目录不存在\n{output_dir}", "red")
        return

    # 使用Windows资源管理器打开目录
    try:
        os.startfile(output_dir)  # 直接调用系统默认方式打开目录
        output_text.delete(1.0, tk.END)
        output_text.insert(tk.END, f"已打开输出文件夹:\n{output_dir}", "green")
    except Exception as e:
        output_text.delete(1.0, tk.END)
        output_text.insert(tk.END, f"打开文件夹失败:\n{str(e)}", "red")


# {{异步命令执行与UI更新函数 }}
def run_command_async(command):
    """在后台线程执行命令并通过主线程更新UI"""
    result, color = run_system_command(command)
    # 使用after()确保UI更新在主线程执行
    root.after(0, update_output, result, color)


def update_output(result, color):
    """更新输出文本并恢复按钮状态"""
    # 补充输出结果信息
    if color == "green":
        apk_output = os.path.splitext(file_path_var.get())[0] + "_universal.apks"
        result += f"\n\nAPK生成成功：\n{apk_output}"
    output_text.insert(tk.END, result)
    output_text.tag_add("color", 1.0, tk.END)
    output_text.tag_config("color", foreground=color)
    # 恢复按钮状态
    run_btn.config(state="normal")


# {{配置文件处理函数 }}
def load_config():
    """加载保存的配置文件（config.json）"""
    config_path = get_resource_path('config.json')
    # 输出配置文件路径
    output_text.insert(tk.END, f"配置文件：{str(config_path)}")
    try:
        if os.path.exists(config_path):
            with open(config_path, 'r', encoding='utf-8') as f:
                return json.load(f)  # 返回配置字典
    except (json.JSONDecodeError, Exception) as e:
        print(f"配置文件加载失败: {e}")  # 配置文件损坏时使用默认值
    return {}  # 返回空字典表示无配置


def save_config(file_key, config_data):
    """保存配置到文件（config.json）"""
    config_path = get_resource_path('config.json')
    try:
        # 先加载现有配置
        existing_config = load_config()
        # 按文件名存储新配置
        existing_config[file_key] = config_data
        existing_config["last_file_key"] = file_key
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(existing_config, f, indent=2, ensure_ascii=False)  # 格式化保存
    except Exception as e:
        print(f"配置文件保存失败: {e}")


# {{签名文件选择函数 }}
def select_keystore():
    """打开密钥库文件选择对话框"""
    keystore_path = filedialog.askopenfilename(
        title="选择密钥库文件",
        filetypes=[("Keystore文件", "*.keystore;*.jks"), ("所有文件", "*.*")]
    )
    if keystore_path:
        # {{根据文件名加载签名配置 }}
        keystore_path_var.set(keystore_path)

        file_key = os.path.basename(keystore_path)  # 使用文件名作为配置键（不含路径）
        configs = load_config()  # 加载所有配置
        if file_key in configs:
            # 加载该文件对应的签名配置
            config = configs[file_key]
            # keystore_path_var.set(config.get('keystore_path', ''))
            key_alias_var.set(config.get('key_alias', ''))
            ks_pass_var.set(config.get('ks_pass', ''))
            key_pass_var.set(config.get('key_pass', ''))
        else:
            # 无对应配置，清空签名输入框
            # keystore_path_var.set('')
            key_alias_var.set('')
            ks_pass_var.set('')
            key_pass_var.set('')


# {{文件选择函数 }}
def select_file():
    """打开文件选择对话框并更新文件路径"""
    file_path = filedialog.askopenfilename(
        title="选择文件",
        filetypes=[("所有文件", "*.*"), ("文本文件", "*.txt"), ("Python文件", "*.py")]  # 可自定义文件类型
    )
    if file_path:  # 如果用户选择了文件
        file_path_var.set(file_path)  # 更新文件路径变量


# 执行系统指令的函数
def run_system_command(command):
    try:
        # 执行指令并捕获输出（stdout=标准输出，stderr=错误输出）
        result = subprocess.run(
            command,
            shell=True,  # 允许使用shell语法（如管道、通配符）
            check=True,  # 若指令返回非0退出码则抛出异常
            stdout=subprocess.PIPE,  # 捕获标准输出
            stderr=subprocess.PIPE,  # 捕获错误输出
            text=True  # 输出以字符串形式返回（而非字节流）
        )
        # 返回成功信息和输出
        return f"指令执行成功:\n{result.stdout}", "green"
    except subprocess.CalledProcessError as e:
        # 指令执行失败（返回非0退出码）
        return f"指令执行失败:\n错误码: {e.returncode}\n错误信息: {e.stderr}", "red"
    except Exception as e:
        # 其他异常（如指令不存在）
        return f"发生异常:\n{str(e)}", "red"


# GUI界面中触发指令执行的函数
def execute_command():
    # 获取选中的AAB文件路径
    aab_path = file_path_var.get()
    output_text.delete(1.0, tk.END)  # 清空现有输出
    # {{获取签名配置参数 }}
    keystore_path = keystore_path_var.get()
    key_alias = key_alias_var.get().strip()
    ks_pass = ks_pass_var.get().strip()
    key_pass = key_pass_var.get().strip()

    output_text.delete(1.0, tk.END)  # 清空现有输出

    # {{签名配置验证 }}
    if not keystore_path:
        output_text.insert(tk.END, "错误：请选择密钥库文件", "red")
        return
    if not os.path.exists(keystore_path):
        output_text.insert(tk.END, f"错误：密钥库文件不存在\n{keystore_path}", "red")
        return
    if not key_alias:
        output_text.insert(tk.END, "错误：请输入密钥别名", "red")
        return
    if not ks_pass or not key_pass:
        output_text.insert(tk.END, "错误：请输入密钥库密码和密钥密码", "red")
        return

    # {{保存当前签名配置到文件 }}
    file_key = os.path.basename(keystore_path)  # 使用文件名作为配置键
    config_data = {
        'keystore_path': keystore_path,
        'key_alias': key_alias,
        'ks_pass': ks_pass,
        'key_pass': key_pass
    }
    save_config(file_key, config_data)  # 验证通过后保存配置

    # 检查文件是否选择
    if not aab_path:
        output_text.insert(tk.END, "错误：请先选择AAB文件", "red")
        return

    # 检查文件扩展名
    if not aab_path.lower().endswith(".aab"):
        output_text.insert(tk.END, "错误：请选择扩展名为.aab的文件", "red")
        return

    # 构建输出APK路径（在AAB同目录生成通用APK）
    apk_output = os.path.splitext(aab_path)[0] + "_universal.apks"

    # {{ 修改：构建带签名参数的bundletool命令 }}
    command = (
        f"java -jar {bundletoolName} build-apks "
        f"--bundle=\"{aab_path}\" "
        f"--output=\"{apk_output}\" "
        # f"--mode=universal "
        f"--ks=\"{keystore_path}\" "  # 密钥库路径
        f"--ks-key-alias={key_alias} "  # 密钥别名
        f"--ks-pass=pass:{ks_pass} "  # 密钥库密码
        f"--key-pass=pass:{key_pass}"  # 密钥密码
    )

    # {{ 修改：异步执行命令 }}
    output_text.insert(tk.END, f"正在执行命令...\n{command}\n\n", "blue")
    run_btn.config(state="disabled")  # 禁用按钮防止重复提交
    # 启动后台线程执行命令
    threading.Thread(target=run_command_async, args=(command,), daemon=True).start()
    # output_text.insert(tk.END, command, "green")
    # # 执行转换命令（保持不变）
    # result, color = run_system_command(command)
    #
    # # 补充输出结果信息（保持不变）
    # if color == "green":
    #     result += f"\n\nAPK生成成功：\n{apk_output}"
    # output_text.insert(tk.END, result)
    # output_text.tag_add("color", 1.0, tk.END)
    # output_text.tag_config("color", foreground=color)


# {{安装APK函数 }}
def install_apk():
    """安装APK文件到连接的设备"""
    apk_path = file_path_var.get()
    output_text.delete(1.0, tk.END)  # 清空现有输出

    # 检查文件是否选择
    if not apk_path:
        output_text.insert(tk.END, "错误：请先选择APK文件", "red")
        return

    # 检查文件扩展名
    if not apk_path.lower().endswith(".apks"):
        output_text.insert(tk.END, "错误：请选择扩展名为.apks的文件", "red")
        return

    # 构建安装命令
    command = f"java -jar {bundletoolName} install-apks --apks={apk_path}"

    # 异步执行命令
    output_text.insert(tk.END, f"正在执行安装命令...\n{command}\n\n", "blue")
    run_btn.config(state="disabled")  # 禁用按钮防止重复提交
    # 启动后台线程执行命令
    threading.Thread(target=run_command_async, args=(command,), daemon=True).start()


# {{选择APK文件函数 }}
def select_apk_file():
    """打开APK文件选择对话框"""
    file_path = filedialog.askopenfilename(
        title="选择APK文件",
        filetypes=[("所有文件", "*.*"), ("aab", "*.aab"), ("APK集文件", "*.apks")]
    )
    if file_path:  # 如果用户选择了文件
        file_path_var.set(file_path)  # 更新文件路径变量


# 创建GUI界面
def create_gui():
    global root, run_btn  # {{全局root和按钮引用 }}
    root = tk.Tk()
    root.title("AAB转APK工具")
    root.geometry("600x400")

    # {{按钮区域框架 }}
    btn_frame = ttk.Frame(root)
    btn_frame.pack(pady=10)

    # 执行按钮（移动到按钮框架内）
    run_btn = ttk.Button(btn_frame, text="AAB转APK", command=execute_command)
    run_btn.pack(side="left", padx=5)

    # {{打开输出文件夹按钮 }}
    open_folder_btn = ttk.Button(btn_frame, text="打开输出文件夹", command=open_output_folder)
    open_folder_btn.pack(side="left", padx=5)

    # {{新增：安装APK按钮 }}
    install_btn = ttk.Button(btn_frame, text="安装APK", command=install_apk)
    install_btn.pack(side="left", padx=5)

    # {{文件选择区域 }}
    # 创建文件选择框架
    file_frame = ttk.LabelFrame(root, text="文件选择")
    file_frame.pack(fill="x", padx=10, pady=5)

    # 文件路径变量
    global file_path_var
    file_path_var = tk.StringVar()

    # 文件路径显示框（只读）
    file_entry = ttk.Entry(file_frame, textvariable=file_path_var, width=50, state="readonly")
    file_entry.pack(side="left", padx=5, pady=5, fill="x", expand=True)

    # 文件选择按钮
    select_btn = ttk.Button(file_frame, text="浏览...", command=select_apk_file)
    select_btn.pack(side="right", padx=5, pady=5)

    # {{签名配置区域 }}
    sign_frame = ttk.LabelFrame(root, text="签名配置（密钥库）")
    sign_frame.pack(fill="x", padx=10, pady=5)

    # 密钥库路径变量
    global keystore_path_var, key_alias_var, ks_pass_var, key_pass_var
    keystore_path_var = tk.StringVar()
    key_alias_var = tk.StringVar()
    ks_pass_var = tk.StringVar()
    key_pass_var = tk.StringVar()

    # 密钥库路径选择
    ttk.Label(sign_frame, text="密钥库路径:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
    ttk.Entry(sign_frame, textvariable=keystore_path_var, width=40).grid(row=0, column=1, padx=5, pady=5, sticky="ew")
    ttk.Button(sign_frame, text="浏览...", command=select_keystore).grid(row=0, column=2, padx=5, pady=5)

    # 密钥别名
    ttk.Label(sign_frame, text="密钥别名:").grid(row=1, column=0, padx=5, pady=5, sticky="w")
    ttk.Entry(sign_frame, textvariable=key_alias_var, width=40).grid(row=1, column=1, padx=5, pady=5, sticky="ew")

    # 密钥库密码
    ttk.Label(sign_frame, text="密钥库密码:").grid(row=2, column=0, padx=5, pady=5, sticky="w")
    ttk.Entry(sign_frame, textvariable=ks_pass_var, show="*", width=40).grid(row=2, column=1, padx=5, pady=5,
                                                                             sticky="ew")

    # 密钥密码
    ttk.Label(sign_frame, text="密钥密码:").grid(row=3, column=0, padx=5, pady=5, sticky="w")
    ttk.Entry(sign_frame, textvariable=key_pass_var, show="*", width=40).grid(row=3, column=1, padx=5, pady=5,
                                                                              sticky="ew")

    # 设置网格列权重，使输入框自适应宽度
    sign_frame.grid_columnconfigure(1, weight=1)

    # 输出显示区域
    global output_text
    output_text = scrolledtext.ScrolledText(root, wrap=tk.WORD, width=70, height=15)
    output_text.pack(padx=10, pady=10)

    # {{加载保存的配置到输入框 }}
    existing_config = load_config()  # 加载配置文件
    file_key = existing_config.get("last_file_key", "")
    config = existing_config.get(file_key, {})
    keystore_path_var.set(config.get('keystore_path', ''))  # 设置密钥库路径
    key_alias_var.set(config.get('key_alias', ''))  # 设置密钥别名
    ks_pass_var.set(config.get('ks_pass', ''))  # 设置密钥库密码
    key_pass_var.set(config.get('key_pass', ''))  # 设置密钥密码

    root.mainloop()


if __name__ == "__main__":
    create_gui()  # 启动GUI

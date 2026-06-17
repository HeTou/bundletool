import json
import os
import subprocess
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext, ttk


bundletoolName = "bundletool-all-1.18.2.jar"
device_spec = "device-spec.json"
selected_device_serial = ""
selected_device_var = None
device_info_cache = {}


def get_resource_path(relative_path):
    return os.path.join(os.path.abspath("."), relative_path)


def open_output_folder():
    current_path = file_path_var.get()
    if not current_path:
        output_text.delete(1.0, tk.END)
        output_text.insert(tk.END, "错误：请先选择文件", "red")
        return

    output_dir = os.path.dirname(current_path)
    if not os.path.exists(output_dir):
        output_text.delete(1.0, tk.END)
        output_text.insert(tk.END, f"错误：输出目录不存在\n{output_dir}", "red")
        return

    try:
        os.startfile(output_dir)
        output_text.delete(1.0, tk.END)
        output_text.insert(tk.END, f"已打开输出文件夹：\n{output_dir}", "green")
    except Exception as e:
        output_text.delete(1.0, tk.END)
        output_text.insert(tk.END, f"打开文件夹失败：\n{str(e)}", "red")


def run_command_async(command, success_message=None):
    result, color = run_system_command(command)
    root.after(0, update_output, result, color, success_message)


def update_output(result, color, success_message=None):
    if color == "green" and success_message:
        result += f"\n\n{success_message}"

    output_text.insert(tk.END, result)
    output_text.tag_add("color", 1.0, tk.END)
    output_text.tag_config("color", foreground=color)
    run_btn.config(state="normal")


def load_config():
    config_path = get_resource_path("config.json")
    try:
        if os.path.exists(config_path):
            with open(config_path, "r", encoding="utf-8") as f:
                return json.load(f)
    except (json.JSONDecodeError, Exception) as e:
        print(f"配置文件加载失败: {e}")
    return {}


def save_config(file_key, config_data):
    config_path = get_resource_path("config.json")
    try:
        existing_config = load_config()
        existing_config[file_key] = config_data
        existing_config["last_file_key"] = file_key
        with open(config_path, "w", encoding="utf-8") as f:
            json.dump(existing_config, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"配置文件保存失败: {e}")


def select_keystore():
    keystore_path = filedialog.askopenfilename(
        title="选择密钥库文件",
        filetypes=[("Keystore 文件", "*.keystore;*.jks"), ("所有文件", "*.*")],
    )
    if not keystore_path:
        return

    keystore_path_var.set(keystore_path)
    file_key = os.path.basename(keystore_path)
    configs = load_config()
    if file_key in configs:
        config = configs[file_key]
        key_alias_var.set(config.get("key_alias", ""))
        ks_pass_var.set(config.get("ks_pass", ""))
        key_pass_var.set(config.get("key_pass", ""))
    else:
        key_alias_var.set("")
        ks_pass_var.set("")
        key_pass_var.set("")


def run_system_command(command):
    try:
        result = subprocess.run(
            command,
            shell=True,
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        return f"命令执行成功:\n{result.stdout}", "green"
    except subprocess.CalledProcessError as e:
        return (
            f"命令执行失败:\n错误码: {e.returncode}\n错误信息: {e.stderr}",
            "red",
        )
    except Exception as e:
        return f"发生异常:\n{str(e)}", "red"


def adb_shell_getprop(serial, prop):
    try:
        result = subprocess.run(
            f'adb -s "{serial}" shell getprop {prop}',
            shell=True,
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        return result.stdout.strip()
    except Exception:
        return ""


def get_device_info(serial):
    if serial in device_info_cache:
        return device_info_cache[serial]

    brand = adb_shell_getprop(serial, "ro.product.brand")
    manufacturer = adb_shell_getprop(serial, "ro.product.manufacturer")
    model = adb_shell_getprop(serial, "ro.product.model")
    device_name = adb_shell_getprop(serial, "ro.product.device")

    vendor = brand or manufacturer or "Unknown"
    model_name = model or device_name or "Unknown"
    display_name = f"{vendor} {model_name}".strip()
    if display_name.lower() == "unknown unknown":
        display_name = serial

    info = {
        "serial": serial,
        "vendor": vendor,
        "model": model_name,
        "display_name": display_name,
        "display_text": f"{display_name} ({serial})",
    }
    device_info_cache[serial] = info
    return info


def get_device_display_text(serial):
    return get_device_info(serial)["display_text"]


def center_window(window, width, height):
    window.update_idletasks()
    screen_width = window.winfo_screenwidth()
    screen_height = window.winfo_screenheight()
    x = max((screen_width - width) // 2, 0)
    y = max((screen_height - height) // 2, 0)
    window.geometry(f"{width}x{height}+{x}+{y}")


def get_connected_devices():
    try:
        result = subprocess.run(
            "adb devices",
            shell=True,
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"adb devices 执行失败: {e.stderr.strip()}") from e
    except Exception as e:
        raise RuntimeError(f"无法执行 adb devices: {str(e)}") from e

    devices = []
    for line in result.stdout.splitlines()[1:]:
        line = line.strip()
        if not line:
            continue
        parts = line.split()
        if len(parts) >= 2 and parts[1] == "device":
            devices.append(parts[0])
    return devices


def set_current_device(serial):
    global selected_device_serial
    selected_device_serial = serial or ""

    if selected_device_var is None:
        return

    if selected_device_serial:
        selected_device_var.set(f"当前连接设备：{get_device_display_text(selected_device_serial)}")
    else:
        selected_device_var.set("当前连接设备：未选择")


def choose_device_dialog(devices):
    dialog = tk.Toplevel(root)
    dialog.title("选择设备")
    center_window(dialog, 620, 320)
    dialog.resizable(False, False)
    dialog.transient(root)
    dialog.grab_set()

    ttk.Label(dialog, text="检测到多个设备，请选择目标设备：").pack(
        padx=12, pady=(12, 8), anchor="w"
    )

    selected_var = tk.StringVar(value=devices[0])
    tree = ttk.Treeview(dialog, columns=("model", "serial"), show="headings", height=min(len(devices), 10))
    tree.heading("model", text="设备")
    tree.heading("serial", text="Serial")
    tree.column("model", width=360, anchor="w")
    tree.column("serial", width=220, anchor="w")
    for serial in devices:
        info = get_device_info(serial)
        tree.insert("", tk.END, iid=serial, values=(info["display_name"], info["serial"]))
    default_index = 0
    if selected_device_serial in devices:
        default_index = devices.index(selected_device_serial)
    default_serial = devices[default_index]
    tree.selection_set(default_serial)
    tree.focus(default_serial)
    tree.pack(fill="both", expand=True, padx=12, pady=4)

    def confirm():
        selection = tree.selection()
        if not selection:
            messagebox.showwarning("选择设备", "请选择一个设备。", parent=dialog)
            return
        selected_var.set(selection[0])
        dialog.destroy()

    def cancel():
        selected_var.set("")
        dialog.destroy()

    def handle_double_click(_event):
        confirm()

    tree.bind("<Double-1>", handle_double_click)

    btn_frame = ttk.Frame(dialog)
    btn_frame.pack(fill="x", padx=12, pady=12)
    ttk.Button(btn_frame, text="确定", command=confirm).pack(side="right", padx=4)
    ttk.Button(btn_frame, text="取消", command=cancel).pack(side="right", padx=4)

    dialog.protocol("WM_DELETE_WINDOW", cancel)
    dialog.wait_window()
    return selected_var.get()


def refresh_device_status():
    output_text.delete(1.0, tk.END)
    try:
        devices = get_connected_devices()
    except RuntimeError as e:
        set_current_device("")
        output_text.insert(tk.END, str(e), "red")
        return

    if not devices:
        set_current_device("")
        output_text.insert(tk.END, "未检测到已连接的设备", "red")
        return

    if len(devices) == 1:
        set_current_device(devices[0])
        output_text.insert(tk.END, f"检测到 1 台设备：{get_device_display_text(devices[0])}", "green")
        return

    if selected_device_serial in devices:
        set_current_device(selected_device_serial)
        output_text.insert(
            tk.END,
            f"检测到 {len(devices)} 台设备，当前设备：{get_device_display_text(selected_device_serial)}",
            "green",
        )
        return

    set_current_device(devices[0])
    output_text.insert(
        tk.END,
        f"检测到 {len(devices)} 台设备，未选择设备时已自动选中第一台：{get_device_display_text(devices[0])}",
        "green",
    )


def choose_current_device():
    output_text.delete(1.0, tk.END)
    try:
        devices = get_connected_devices()
    except RuntimeError as e:
        set_current_device("")
        output_text.insert(tk.END, str(e), "red")
        return

    if not devices:
        set_current_device("")
        output_text.insert(tk.END, "未检测到已连接的设备", "red")
        return

    if len(devices) == 1:
        set_current_device(devices[0])
        output_text.insert(tk.END, f"当前仅连接 1 台设备：{get_device_display_text(devices[0])}", "green")
        return

    selected = choose_device_dialog(devices)
    if not selected:
        output_text.insert(tk.END, "已取消设备选择", "red")
        return

    set_current_device(selected)
    output_text.insert(tk.END, f"已选择设备：{get_device_display_text(selected)}", "green")


def ensure_target_device():
    try:
        devices = get_connected_devices()
    except RuntimeError as e:
        output_text.insert(tk.END, str(e), "red")
        return None

    if not devices:
        output_text.insert(tk.END, "错误：未检测到已连接的设备", "red")
        set_current_device("")
        return None

    if len(devices) == 1:
        set_current_device(devices[0])
        return devices[0]

    if selected_device_serial in devices:
        set_current_device(selected_device_serial)
        return selected_device_serial

    selected = choose_device_dialog(devices)
    if not selected:
        output_text.insert(tk.END, "已取消设备选择", "red")
        return None

    set_current_device(selected)
    return selected


def execute_command():
    aab_path = file_path_var.get()
    output_text.delete(1.0, tk.END)

    keystore_path = keystore_path_var.get()
    key_alias = key_alias_var.get().strip()
    ks_pass = ks_pass_var.get().strip()
    key_pass = key_pass_var.get().strip()

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
    if not aab_path:
        output_text.insert(tk.END, "错误：请先选择 AAB 文件", "red")
        return
    if not aab_path.lower().endswith(".aab"):
        output_text.insert(tk.END, "错误：请选择扩展名为 .aab 的文件", "red")
        return

    file_key = os.path.basename(keystore_path)
    save_config(
        file_key,
        {
            "keystore_path": keystore_path,
            "key_alias": key_alias,
            "ks_pass": ks_pass,
            "key_pass": key_pass,
        },
    )

    apk_output = os.path.splitext(aab_path)[0] + "_universal.apks"
    command = f"java -jar {bundletoolName} build-apks "

    if os.path.exists(device_spec) and os.path.getsize(device_spec) > 0:
        command += f'--device-spec="{device_spec}" '

    command += (
        f'--bundle="{aab_path}" '
        f'--output="{apk_output}" '
        f'--ks="{keystore_path}" '
        f"--ks-key-alias={key_alias} "
        f"--ks-pass=pass:{ks_pass} "
        f"--key-pass=pass:{key_pass}"
    )

    output_text.insert(tk.END, f"正在执行命令...\n{command}\n\n", "blue")
    run_btn.config(state="disabled")
    threading.Thread(
        target=run_command_async,
        args=(command, f"APK 生成成功：\n{apk_output}"),
        daemon=True,
    ).start()


def install_apk():
    apk_path = file_path_var.get()
    output_text.delete(1.0, tk.END)

    if not apk_path:
        output_text.insert(tk.END, "错误：请先选择 APKS 文件", "red")
        return
    if not apk_path.lower().endswith(".apks"):
        output_text.insert(tk.END, "错误：请选择扩展名为 .apks 的文件", "red")
        return

    target_device = ensure_target_device()
    if not target_device:
        return

    command = (
        f'java -jar {bundletoolName} install-apks '
        f'--apks="{apk_path}" '
        f"--device-id={target_device}"
    )

    output_text.insert(
        tk.END,
        f"正在执行安装命令...\n目标设备：{get_device_display_text(target_device)}\n{command}\n\n",
        "blue",
    )
    run_btn.config(state="disabled")
    threading.Thread(
        target=run_command_async,
        args=(command, f"安装完成，目标设备：{get_device_display_text(target_device)}"),
        daemon=True,
    ).start()


def select_apk_file():
    file_path = filedialog.askopenfilename(
        title="选择文件",
        filetypes=[("所有文件", "*.*"), ("AAB 文件", "*.aab"), ("APKS 文件", "*.apks")],
    )
    if file_path:
        file_path_var.set(file_path)


def create_gui():
    global root, run_btn, selected_device_var

    root = tk.Tk()
    root.title("AAB转APK工具")
    root.geometry("760x520")

    selected_device_var = tk.StringVar()
    set_current_device("")

    header_frame = ttk.Frame(root)
    header_frame.pack(fill="x", padx=10, pady=(10, 0))

    device_label = ttk.Label(
        header_frame,
        textvariable=selected_device_var,
        foreground="#0b57d0",
        cursor="hand2",
    )
    device_label.pack(side="left")
    device_label.bind("<Button-1>", lambda event: choose_current_device())

    ttk.Button(header_frame, text="刷新设备", command=refresh_device_status).pack(side="right")

    btn_frame = ttk.Frame(root)
    btn_frame.pack(pady=10)

    run_btn = ttk.Button(btn_frame, text="AAB转APKS", command=execute_command)
    run_btn.pack(side="left", padx=5)
    ttk.Button(btn_frame, text="打开输出文件夹", command=open_output_folder).pack(side="left", padx=5)
    ttk.Button(btn_frame, text="安装APKS", command=install_apk).pack(side="left", padx=5)

    file_frame = ttk.LabelFrame(root, text="文件选择")
    file_frame.pack(fill="x", padx=10, pady=5)

    global file_path_var
    file_path_var = tk.StringVar()

    ttk.Entry(file_frame, textvariable=file_path_var, width=70, state="readonly").pack(
        side="left", padx=5, pady=5, fill="x", expand=True
    )
    ttk.Button(file_frame, text="浏览...", command=select_apk_file).pack(side="right", padx=5, pady=5)

    sign_frame = ttk.LabelFrame(root, text="签名配置（密钥库）")
    sign_frame.pack(fill="x", padx=10, pady=5)

    global keystore_path_var, key_alias_var, ks_pass_var, key_pass_var
    keystore_path_var = tk.StringVar()
    key_alias_var = tk.StringVar()
    ks_pass_var = tk.StringVar()
    key_pass_var = tk.StringVar()

    ttk.Label(sign_frame, text="密钥库路径:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
    ttk.Entry(sign_frame, textvariable=keystore_path_var, width=52).grid(
        row=0, column=1, padx=5, pady=5, sticky="ew"
    )
    ttk.Button(sign_frame, text="浏览...", command=select_keystore).grid(row=0, column=2, padx=5, pady=5)

    ttk.Label(sign_frame, text="密钥别名:").grid(row=1, column=0, padx=5, pady=5, sticky="w")
    ttk.Entry(sign_frame, textvariable=key_alias_var, width=52).grid(
        row=1, column=1, padx=5, pady=5, sticky="ew"
    )

    ttk.Label(sign_frame, text="密钥库密码:").grid(row=2, column=0, padx=5, pady=5, sticky="w")
    ttk.Entry(sign_frame, textvariable=ks_pass_var, show="*", width=52).grid(
        row=2, column=1, padx=5, pady=5, sticky="ew"
    )

    ttk.Label(sign_frame, text="密钥密码:").grid(row=3, column=0, padx=5, pady=5, sticky="w")
    ttk.Entry(sign_frame, textvariable=key_pass_var, show="*", width=52).grid(
        row=3, column=1, padx=5, pady=5, sticky="ew"
    )

    sign_frame.grid_columnconfigure(1, weight=1)

    global output_text
    output_text = scrolledtext.ScrolledText(root, wrap=tk.WORD, width=90, height=16)
    output_text.pack(padx=10, pady=10, fill="both", expand=True)

    existing_config = load_config()
    file_key = existing_config.get("last_file_key", "")
    config = existing_config.get(file_key, {})
    keystore_path_var.set(config.get("keystore_path", ""))
    key_alias_var.set(config.get("key_alias", ""))
    ks_pass_var.set(config.get("ks_pass", ""))
    key_pass_var.set(config.get("key_pass", ""))

    refresh_device_status()
    root.mainloop()


if __name__ == "__main__":
    create_gui()

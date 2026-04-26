import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import threading
import subprocess
import os
import re

class VideoCutApp:
    def __init__(self, root):
        self.root = root
        self.root.title("视频裁剪工具（终极版）")
        self.root.geometry("520x320")

        self.video_path = tk.StringVar()

        # 选择视频
        tk.Label(root, text="视频文件：").place(x=30, y=30)
        tk.Entry(root, textvariable=self.video_path, width=50).place(x=100, y=30)
        tk.Button(root, text="选择", command=self.select_video).place(x=420, y=28)

        # 开头
        tk.Label(root, text="剪掉开头(秒)：").place(x=30, y=80)
        self.entry_start = tk.Entry(root, width=10)
        self.entry_start.place(x=140, y=80)
        self.entry_start.insert(0, "0")

        # 结尾
        tk.Label(root, text="剪掉结尾(秒)：").place(x=260, y=80)
        self.entry_end = tk.Entry(root, width=10)
        self.entry_end.place(x=370, y=80)
        self.entry_end.insert(0, "0")

        # 按钮
        self.btn_cut = tk.Button(root, text="开始裁剪", bg="#0099cc",
                                 fg="white", width=20, height=2,
                                 command=self.start_thread)
        self.btn_cut.place(x=160, y=130)

        # 状态
        self.status = tk.Label(root, text="等待操作...")
        self.status.place(x=220, y=200)

        # 进度条
        self.progress = ttk.Progressbar(root, length=300)
        self.progress.place(x=110, y=230)

    def select_video(self):
        path = filedialog.askopenfilename(filetypes=[("MP4视频", "*.mp4")])
        if path:
            self.video_path.set(path)

    def start_thread(self):
        threading.Thread(target=self.cut_video).start()

    def update_ui(self, percent, text):
        self.progress["value"] = percent
        self.status.config(text=text)
        self.root.update_idletasks()

    def get_video_duration(self, path):
        cmd = [
            "ffprobe", "-v", "error",
            "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1",
            path
        ]
        result = subprocess.run(cmd, stdout=subprocess.PIPE, text=True)
        return float(result.stdout.strip())

    def cut_video(self):
        self.btn_cut.config(state="disabled")

        video_path = self.video_path.get().strip()
        if not video_path:
            messagebox.showerror("错误", "请选择视频")
            self.btn_cut.config(state="normal")
            return

        try:
            cut_start = float(self.entry_start.get())
            cut_end = float(self.entry_end.get())
        except:
            messagebox.showerror("错误", "请输入数字")
            self.btn_cut.config(state="normal")
            return

        try:
            duration = self.get_video_duration(video_path)
            start = cut_start
            end = duration - cut_end

            if start >= end:
                messagebox.showerror("错误", "时间范围错误")
                self.btn_cut.config(state="normal")
                return

            # 自动路径
            base, ext = os.path.splitext(video_path)
            save_path = base + "_cut.mp4"
            i = 1
            while os.path.exists(save_path):
                save_path = f"{base}_cut_{i}.mp4"
                i += 1

            # ffmpeg命令
            cmd = [
                "ffmpeg",
                "-y",
                "-ss", str(start),
                "-to", str(end),
                "-i", video_path,
                "-c", "copy",
                save_path
            ]

            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                encoding="utf-8"
            )

            time_pattern = re.compile(r"time=(\d+):(\d+):(\d+\.\d+)")

            while True:
                line = process.stdout.readline()
                if not line:
                    break

                match = time_pattern.search(line)
                if match:
                    h, m, s = match.groups()
                    current_time = int(h)*3600 + int(m)*60 + float(s)
                    percent = min((current_time / (end - start)) * 100, 100)
                    self.update_ui(percent, f"处理中：{int(percent)}%")

            process.wait()

            self.update_ui(100, "完成！")
            messagebox.showinfo("完成", f"保存路径：\n{save_path}")

        except Exception as e:
            messagebox.showerror("错误", str(e))

        self.btn_cut.config(state="normal")


if __name__ == "__main__":
    root = tk.Tk()
    app = VideoCutApp(root)
    root.mainloop()
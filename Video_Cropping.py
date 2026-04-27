import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import threading
import subprocess
import shutil
import os
import re

class VideoCutApp:
    def __init__(self, root):
        self.root = root
        self.root.title("视频裁剪工具 v2.0")
        self.root.geometry("520x320")

        self.video_path = tk.StringVar()

        # 选择视频
        tk.Label(root, text="视频文件：").place(x=30, y=30)
        tk.Entry(root, textvariable=self.video_path, width=50).place(x=100, y=30)
        tk.Button(root, text="选择", command=self.select_video).place(x=420, y=28)

        # 保留开始时间
        tk.Label(root, text="保留开始：").place(x=30, y=80)
        self.entry_deletestart = tk.Entry(root, width=12)
        self.entry_deletestart.place(x=120, y=80)
        self.entry_deletestart.insert(0, "00:00:00")

        # 保留结束时间
        tk.Label(root, text="保留结束：").place(x=260, y=80)
        self.entry_deleteend = tk.Entry(root, width=12)
        self.entry_deleteend.place(x=340, y=80)
        self.entry_deleteend.insert(0, "00:00:00")

        tk.Label(root, text="(格式: HH:MM:SS)").place(x=420, y=80)

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

    def parse_time(self, time_str):
        time_str = time_str.strip()
        parts = time_str.split(":")
        if len(parts) == 3:
            h, m, s = parts
            return int(h) * 3600 + int(m) * 60 + float(s)
        elif len(parts) == 2:
            m, s = parts
            return int(m) * 60 + float(s)
        return float(time_str)

    def cut_video(self):
        self.btn_cut.config(state="disabled")

        video_path = self.video_path.get().strip()
        if not video_path:
            messagebox.showerror("错误", "请选择视频")
            self.btn_cut.config(state="normal")
            return

        delete_start_str = self.entry_deletestart.get().strip()
        delete_end_str = self.entry_deleteend.get().strip()

        try:
            duration = self.get_video_duration(video_path)

            delete_start = self.parse_time(delete_start_str) if delete_start_str else 0
            delete_end = self.parse_time(delete_end_str) if delete_end_str else 0

            if delete_start == 0 and delete_end == 0:
                messagebox.showerror("错误", "删除时间不能为 0")
                self.btn_cut.config(state="normal")
                return

            if delete_start >= delete_end and delete_end > 0:
                messagebox.showerror("错误", "删除时间段重叠或空")
                self.btn_cut.config(state="normal")
                return

            if delete_start > duration or delete_end > duration:
                messagebox.showerror("错误", "时间超出视频范围")
                self.btn_cut.config(state="normal")
                return

            base, ext = os.path.splitext(video_path)
            save_path = base + "_cut.mp4"
            i = 1
            while os.path.exists(save_path):
                save_path = f"{base}_cut_{i}.mp4"
                i += 1

            has_start = delete_start > 0
            has_end = delete_end > 0 and delete_end < duration

            if has_start and has_end:
                cmd = [
                    "ffmpeg", "-y",
                    "-ss", str(delete_start), "-to", str(delete_end),
                    "-i", video_path,
                    "-c", "copy",
                    save_path
                ]
            elif has_start:
                cmd = [
                    "ffmpeg", "-y",
                    "-ss", str(delete_start), "-to", str(duration),
                    "-i", video_path,
                    "-c", "copy",
                    save_path
                ]
            elif has_end:
                cmd = [
                    "ffmpeg", "-y",
                    "-ss", "0", "-to", str(delete_end),
                    "-i", video_path,
                    "-c", "copy",
                    save_path
                ]
            else:
                shutil.copy2(video_path, save_path)

            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode != 0:
                messagebox.showerror("错误", f"处理失败: {result.stderr}")
                self.btn_cut.config(state="normal")
                return

            self.update_ui(100, "完成！")
            messagebox.showinfo("完成", f"保存路径：\n{save_path}")

        except Exception as e:
            messagebox.showerror("错误", str(e))

        self.btn_cut.config(state="normal")


if __name__ == "__main__":
    root = tk.Tk()
    app = VideoCutApp(root)
    root.mainloop()
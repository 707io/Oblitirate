import os
import sys
import shutil
import subprocess
import ctypes
import json
import customtkinter as ctk
from tkinter import filedialog, messagebox
from send2trash import send2trash
from datetime import datetime

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin() != 0
    except Exception:
        return False

def relaunch_as_admin():
    params = " ".join([f'"{arg}"' for arg in sys.argv])
    ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, params, None, 1)
    sys.exit()

class ObliterateApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Obliterate - Force Delete Tool")
        self.geometry("920x580")
        self.resizable(False, False)

        self.selected_paths = {}
        self.skip_confirm = ctk.BooleanVar(value=False)
        self.use_recycle_bin = ctk.BooleanVar(value=True)
        self.select_all_var = ctk.BooleanVar(value=False)
        self.power_user_mode = ctk.BooleanVar(value=False)
        self.logs_visible = True

        self.build_ui()
        self.load_selection()
        self.update_admin_status()

    def build_ui(self):
        self.main_frame = ctk.CTkFrame(self)
        self.main_frame.pack(fill="both", expand=True, padx=8, pady=8)

        self.left_frame = ctk.CTkFrame(self.main_frame, width=580)
        self.left_frame.pack(side="left", fill="both", expand=True, padx=(0, 4))

        self.right_frame = ctk.CTkFrame(self.main_frame, width=320)
        self.right_frame.pack(side="right", fill="y")

        # Left Panel
        ctk.CTkLabel(self.left_frame, text="🧨Obliterate - Force Delete Tool", font=("Segoe UI", 24, "bold")).pack(pady=(12, 0))
        ctk.CTkLabel(self.left_frame, text="Created by 707", font=("Segoe UI", 12)).pack(pady=(0, 10))

        self.listbox_frame = ctk.CTkScrollableFrame(self.left_frame, height=140)
        self.listbox_frame.pack(padx=8, pady=(0, 5), fill="x")

        self.select_all_cb = ctk.CTkCheckBox(self.left_frame, text="Select All",
                                             variable=self.select_all_var, command=self.toggle_select_all)
        self.select_all_cb.pack(pady=(0, 5))

        btn_frame = ctk.CTkFrame(self.left_frame)
        btn_frame.pack(pady=4)

        ctk.CTkButton(btn_frame, text="📄File", width=75, command=self.select_file_only).grid(row=0, column=0, padx=5)
        ctk.CTkButton(btn_frame, text="📁Folder", width=75, command=self.select_folder_only).grid(row=0, column=1, padx=5)
        ctk.CTkButton(btn_frame, text="❌Remove", width=75, command=self.remove_selected).grid(row=0, column=2, padx=5)
        ctk.CTkButton(btn_frame, text="🧹Clear list", width=75, command=self.clear_list).grid(row=0, column=3, padx=5)

        ctk.CTkCheckBox(self.left_frame, text="🗑️Recycle Bin", variable=self.use_recycle_bin).pack(pady=(10, 2))
        ctk.CTkCheckBox(self.left_frame, text="✅Don't ask again", variable=self.skip_confirm).pack(pady=(0, 2))
        ctk.CTkCheckBox(self.left_frame, text="⚡Power User Mode (Admin)", variable=self.power_user_mode).pack(pady=(0, 8))

        self.status_admin_label = ctk.CTkLabel(self.left_frame, text="", font=("Segoe UI", 10, "italic"))
        self.status_admin_label.pack(pady=(0, 10))

        ctk.CTkButton(self.left_frame, text="🔥OBLITERATE", command=self.delete_selected,
                      fg_color="#C62828", hover_color="#B71C1C", font=("Segoe UI", 15, "bold"),
                      height=35).pack(pady=(5, 8), ipadx=5)

        self.status_label = ctk.CTkLabel(self.left_frame, text="🟢Ready", text_color="gray", font=("Segoe UI", 11))
        self.status_label.pack()

        # Right Panel: Logs
        self.toggle_btn = ctk.CTkButton(self.right_frame, text="▼ Hide Logs", width=60, height=25, font=("Segoe UI", 12),
                                        command=self.toggle_logs)
        self.toggle_btn.pack(pady=(8, 5))

        self.log_title = ctk.CTkLabel(self.right_frame, text="📝Logs", font=("Segoe UI", 18, "bold"))
        self.log_title.pack(pady=(0, 4))

        self.logbox = ctk.CTkTextbox(self.right_frame, height=520, font=("Consolas", 9), state="disabled", wrap="none")
        self.logbox.pack(padx=8, pady=(0, 10), fill="both", expand=True)

    def save_selection(self):
        try:
            save_dir = os.path.join(os.getenv("APPDATA"), "Obliterate")
            os.makedirs(save_dir, exist_ok=True)
            save_path = os.path.join(save_dir, "selection.json")
            with open(save_path, "w", encoding="utf-8") as f:
                json.dump(list(self.selected_paths.keys()), f)
        except Exception as e:
            print("Error saving selection:", e)

    def load_selection(self):
        try:
            save_path = os.path.join(os.getenv("APPDATA"), "Obliterate", "selection.json")
            if os.path.exists(save_path):
                with open(save_path, "r", encoding="utf-8") as f:
                    paths = json.load(f)
                for p in paths:
                    if p not in self.selected_paths:
                        self.selected_paths[p] = ctk.BooleanVar(value=False)
                self.update_listbox()
        except Exception as e:
            print("Error loading selection:", e)

    def update_admin_status(self):
        if is_admin():
            self.status_admin_label.configure(text="🛡️Running with Administrator privileges", text_color="green")
        else:
            self.status_admin_label.configure(text="⚠Not running as Administrator", text_color="orange")

    def toggle_logs(self):
        if self.logs_visible:
            self.logbox.pack_forget()
            self.log_title.pack_forget()
            self.toggle_btn.configure(text="▶ Show Logs")
            self.right_frame.configure(width=50)
        else:
            self.log_title.pack(pady=(0, 4))
            self.logbox.pack(padx=8, pady=(0, 10), fill="both", expand=True)
            self.toggle_btn.configure(text="▼ Hide Logs")
            self.right_frame.configure(width=320)
        self.logs_visible = not self.logs_visible

    def toggle_select_all(self):
        for var in self.selected_paths.values():
            var.set(self.select_all_var.get())

    def select_file_only(self):
        path = filedialog.askopenfilename(title="Select file")
        if path and path not in self.selected_paths:
            self.selected_paths[path] = ctk.BooleanVar(value=False)
            self.update_listbox()
            self.save_selection()

    def select_folder_only(self):
        folder = filedialog.askdirectory(title="Select folder")
        if folder and folder not in self.selected_paths:
            self.selected_paths[folder] = ctk.BooleanVar(value=False)
            self.update_listbox()
            self.save_selection()

    def clear_list(self):
        self.selected_paths.clear()
        self.update_listbox()
        self.save_selection()

    def remove_selected(self):
        to_remove = [path for path, var in self.selected_paths.items() if var.get()]
        for path in to_remove:
            del self.selected_paths[path]
        self.update_listbox()
        self.save_selection()

    def update_listbox(self):
        for widget in self.listbox_frame.winfo_children():
            widget.destroy()

        if not self.selected_paths:
            ctk.CTkLabel(self.listbox_frame, text="(No items)", font=("Consolas", 10)).pack()
        else:
            for path, var in sorted(self.selected_paths.items()):
                frame = ctk.CTkFrame(self.listbox_frame)
                frame.pack(fill="x", padx=3, pady=1)
                ctk.CTkCheckBox(frame, text=path, variable=var).pack(anchor="w")

    def delete_selected(self):
        if not self.selected_paths:
            messagebox.showinfo("Nothing to delete", "Please add files or folders first.")
            return

        if not self.skip_confirm.get():
            confirm = messagebox.askyesno("Confirm Deletion", "Delete selected items?")
            if not confirm:
                return

        results = []
        for path in list(self.selected_paths.keys()):
            try:
                if not os.path.exists(path):
                    results.append(f"⚠ [SKIPPED] Path not found: {path}")
                    continue

                if self.use_recycle_bin.get():
                    send2trash(path)
                    results.append(f"🗑[RECYCLED] {path}")
                else:
                    try:
                        if os.path.isdir(path):
                            shutil.rmtree(path)
                        else:
                            os.remove(path)
                        results.append(f"✔[DELETED] {path}")
                    except Exception:
                        ps_command = f'remove-item -Path "{path}" -Force -Recurse'
                        completed = subprocess.run(
                            ["powershell", "-Command", ps_command],
                            capture_output=True, text=True
                        )
                        if completed.returncode == 0:
                            results.append(f"🛠 [POWERSHELL] {path}")
                        else:
                            if self.power_user_mode.get():
                                if not is_admin():
                                    confirm = messagebox.askyesno(
                                        "Elevation Required",
                                        f"Cannot delete:\n{path}\n\n"
                                        "Relaunch Obliterate with administrator privileges?"
                                    )
                                    if confirm:
                                        self.status_label.configure(text="🟡Requesting admin rights...")
                                        relaunch_as_admin()
                                    results.append(f"🔒[ELEVATION REQUIRED] {path}")
                                    # We exit here to let the elevated instance handle deletion
                                    break
                                else:
                                    results.append(f"❌[FAILED EVEN AS ADMIN] {path}")
                            else:
                                results.append(f"❌[ERROR] Cannot delete: {path}\n{completed.stderr.strip()}")
            except Exception as e:
                results.append(f"❌[ERROR] {path} | {e}")

        self.status_label.configure(text="✅Done")
        self.selected_paths.clear()
        self.update_listbox()
        self.save_selection()
        self.write_log(results)
        self.display_log(results)
        self.update_admin_status()

    def write_log(self, entries):
        log_dir = os.path.join(os.getenv("APPDATA"), "Obliterate")
        os.makedirs(log_dir, exist_ok=True)
        log_path = os.path.join(log_dir, "obliterate.log")

        with open(log_path, "a", encoding="utf-8") as f:
            f.write(f"\n--- {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ---\n")
            for entry in entries:
                f.write(entry + "\n")

    def display_log(self, entries):
        self.logbox.configure(state="normal")
        self.logbox.insert("end", f"\n--- {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ---\n")
        for entry in entries:
            self.logbox.insert("end", entry + "\n")
        self.logbox.insert("end", "\n")
        self.logbox.see("end")
        self.logbox.configure(state="disabled")


if __name__ == "__main__":
    app = ObliterateApp()
    app.lift()
    app.after(100, lambda: app.focus_force())
    app.mainloop()

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
auPunch GUI - UniversalUI Audio Project Slimming Station
Compliant with ATG App Standards and rud() spatial geometry principles.
Inherits UniversalApp (Dark/Light theme, DWM immersive titlebar, DPI scaling,
TSV-based i18n, custom dialogs, live console logger, and non-blocking toast notifications).

Part of ATGprjs MVlab Ecosystem
"""

import os
import sys
import threading
from pathlib import Path
import tkinter as tk
from tkinter import ttk, filedialog

# Add ATGprjs root to sys.path for _lib imports
BASE_DIR = Path(__file__).resolve().parent
for p in [BASE_DIR, BASE_DIR.parent, BASE_DIR.parent.parent]:
    if (p / "_lib").is_dir():
        if str(p) not in sys.path:
            sys.path.insert(0, str(p))
        break

import _lib.UniversalUI as UniversalUI
from _lib import i18n
from i18n import detect_language, get_text, t
from aup3_converter import Aup3Converter
from auPunchLauncher import find_audacity_exe, launch_audacity

class AuPunchGUI:
    """
    auPunch GUI Controller & View
    Manages UI state, responsive layout, background worker threading,
    and external Audacity integration.
    """
    def __init__(self, app_wrapper, default_source="", default_output=""):
        self.app = app_wrapper
        self.root = app_wrapper.root

        # Initialize i18n
        _lang_dir = str(BASE_DIR / "_lang")
        i18n.init(_lang_dir, default_lang="zh_TW", fallback_lang="zh_TW")
        saved_lang = self.app.config.get("language")
        if not saved_lang:
            saved_lang = detect_language()
        i18n.set_language(saved_lang)

        # State Variables
        saved_src = self.app.config.get("last_source", default_source)
        saved_out = self.app.config.get("last_output", default_output)
        saved_fmt = self.app.config.get("format", "flac")
        saved_target = self.app.config.get("target", "ardour")
        saved_edit = self.app.config.get("auto_open", False)
        saved_audacity = self.app.config.get("audacity_path", "")

        # Detect Audacity executable
        detected_audacity = find_audacity_exe(saved_audacity if saved_audacity else None)
        audacity_initial_str = str(detected_audacity) if detected_audacity else ""

        self.source_var = tk.StringVar(value=saved_src)
        self.output_var = tk.StringVar(value=saved_out)
        self.format_var = tk.StringVar(value=saved_fmt)
        self.target_var = tk.StringVar(value=saved_target)
        self.edit_var = tk.BooleanVar(value=saved_edit and bool(detected_audacity))
        self.audacity_path_var = tk.StringVar(value=audacity_initial_str)
        self.status_var = tk.StringVar(value=t('gui_status_ready'))
        self.progress_var = tk.DoubleVar(value=0.0)

        self.available_langs = i18n.get_available_languages()
        self.code_to_display = dict(self.available_langs)
        self.display_to_code = {v: k for k, v in self.available_langs.items()}
        curr_lang = i18n.get_language()
        self.lang_display_var = tk.StringVar(value=self.code_to_display.get(curr_lang, curr_lang))

        self.is_running = False

        # Custom TTK Button styling for Big Punch
        self.app.root.style = ttk.Style()
        palette = UniversalUI.get_palette(is_dark=self.app.is_dark, follow_system_accent=True)
        accent_color = palette.get("accent", "#007acc")
        
        self.app.root.style.configure(
            "BigPunch.TButton",
            font=self.app.font_bold,
            padding=[14, 8],
            background=accent_color,
            foreground="white"
        )
        self.app.root.style.map(
            "BigPunch.TButton",
            background=[('active', palette.get("highlight", "#005fb8")), ('pressed', '#004c99')],
            foreground=[('active', 'white')]
        )

        self._build_ui()
        self.retranslate_ui()

    def _build_ui(self):
        # Master Responsive Container
        self.main_container = ttk.Frame(self.root, padding="14 10 14 10")
        self.main_container.pack(fill=tk.BOTH, expand=True)

        # ── 1. 頂部標頭列 (Header Bar: Title, Slogan & Quick Actions) ──
        self.header_frame = ttk.Frame(self.main_container)
        self.header_frame.pack(fill=tk.X, pady=(0, 10))

        # Header Left: Titles
        hdr_left = ttk.Frame(self.header_frame)
        hdr_left.pack(side=tk.LEFT, fill=tk.X, expand=True)

        self.lbl_title = ttk.Label(hdr_left, text="auPunch", font=self.app.font_h1)
        self.lbl_title.pack(anchor=tk.W)

        self.lbl_slogan1 = ttk.Label(hdr_left, text=t('slogan1'), style="Subtitle.TLabel")
        self.lbl_slogan1.pack(anchor=tk.W, pady=(1, 0))

        self.lbl_slogan2 = ttk.Label(hdr_left, text=t('slogan2'), style="Subtitle.TLabel")
        self.lbl_slogan2.pack(anchor=tk.W, pady=(1, 0))

        self.lbl_subtitle = ttk.Label(hdr_left, text=t('subtitle'), font=self.app.font_std)
        self.lbl_subtitle.pack(anchor=tk.W, pady=(2, 0))

        # Header Right: Actions (Theme Toggle & Language Selector)
        hdr_right = ttk.Frame(self.header_frame)
        hdr_right.pack(side=tk.RIGHT, anchor=tk.NE)

        # Theme toggle button
        self.btn_theme = ttk.Button(
            hdr_right,
            text=t('gui_theme_btn'),
            command=self._toggle_theme,
            padding=[6, 4]
        )
        self.btn_theme.pack(side=tk.LEFT, padx=(0, 6))

        # Language dropdown (Showing readable names)
        self.lang_combo = ttk.Combobox(
            hdr_right,
            textvariable=self.lang_display_var,
            values=list(self.code_to_display.values()),
            width=18,
            state="readonly"
        )
        self.lang_combo.pack(side=tk.LEFT)
        self.lang_combo.bind("<<ComboboxSelected>>", self._on_language_changed)

        # ── 2. 步驟 1: 來源專案群組 (Card 1: Source) ──
        self.grp_source = ttk.LabelFrame(self.main_container, text=t('gui_source_group'), padding=10)
        self.grp_source.pack(fill=tk.X, pady=(0, 8))

        src_row = ttk.Frame(self.grp_source)
        src_row.pack(fill=tk.X)

        self.entry_src = ttk.Entry(src_row, textvariable=self.source_var)
        self.entry_src.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 6))

        self.btn_src_folder = ttk.Button(
            src_row,
            text=t('gui_btn_folder'),
            command=self._choose_folder,
            padding=[8, 4]
        )
        self.btn_src_folder.pack(side=tk.LEFT, padx=(0, 4))

        self.btn_src_archive = ttk.Button(
            src_row,
            text=t('gui_btn_archive'),
            command=self._choose_archive,
            padding=[8, 4]
        )
        self.btn_src_archive.pack(side=tk.LEFT)

        # ── 3. 步驟 2: 轉檔目的地群組 (Card 2: Destination) ──
        self.grp_dest = ttk.LabelFrame(self.main_container, text=t('gui_dest_group'), padding=10)
        self.grp_dest.pack(fill=tk.X, pady=(0, 8))

        dst_row = ttk.Frame(self.grp_dest)
        dst_row.pack(fill=tk.X)

        self.entry_dst = ttk.Entry(dst_row, textvariable=self.output_var)
        self.entry_dst.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 6))

        self.btn_browse_dest = ttk.Button(
            dst_row,
            text=t('gui_btn_browse'),
            command=self._choose_dest,
            padding=[8, 4]
        )
        self.btn_browse_dest.pack(side=tk.LEFT)

        # ── 4. 步驟 3: 轉換與外部編輯設定群組 (Card 3: Options) ──
        self.grp_opts = ttk.LabelFrame(self.main_container, text=t('gui_opt_group'), padding=10)
        self.grp_opts.pack(fill=tk.X, pady=(0, 8))

        # 目標 DAW 格式選擇 (Ardour vs Audacity AUP)
        self.rb_target_ardour = ttk.Radiobutton(
            self.grp_opts,
            text=t('gui_target_ardour'),
            value="ardour",
            variable=self.target_var
        )
        self.rb_target_ardour.pack(anchor=tk.W, pady=(0, 2))

        self.rb_target_aup = ttk.Radiobutton(
            self.grp_opts,
            text=t('gui_target_aup'),
            value="aup",
            variable=self.target_var
        )
        self.rb_target_aup.pack(anchor=tk.W, pady=(0, 6))

        # 分隔線
        sep_target = ttk.Separator(self.grp_opts, orient=tk.HORIZONTAL)
        sep_target.pack(fill=tk.X, pady=4)

        # 格式選擇 (FLAC vs WAV)
        self.rb_flac = ttk.Radiobutton(
            self.grp_opts,
            text=t('gui_fmt_flac'),
            value="flac",
            variable=self.format_var
        )
        self.rb_flac.pack(anchor=tk.W, pady=(0, 3))

        self.rb_wav = ttk.Radiobutton(
            self.grp_opts,
            text=t('gui_fmt_wav'),
            value="wav",
            variable=self.format_var
        )
        self.rb_wav.pack(anchor=tk.W, pady=(0, 6))

        # 分隔線
        sep = ttk.Separator(self.grp_opts, orient=tk.HORIZONTAL)
        sep.pack(fill=tk.X, pady=4)

        # Audacity 連動設定 (外部編輯器)
        self.chk_edit = ttk.Checkbutton(
            self.grp_opts,
            text=t('gui_chk_edit'),
            variable=self.edit_var,
            command=self._on_edit_check_toggled
        )
        self.chk_edit.pack(anchor=tk.W, pady=(2, 4))

        # Audacity 路徑選取列
        aud_row = ttk.Frame(self.grp_opts)
        aud_row.pack(fill=tk.X, pady=(2, 0))

        self.lbl_aud_path = ttk.Label(aud_row, text=t('gui_lbl_audacity_path'))
        self.lbl_aud_path.pack(side=tk.LEFT, padx=(0, 4))

        self.entry_aud = ttk.Entry(aud_row, textvariable=self.audacity_path_var)
        self.entry_aud.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 6))

        self.btn_browse_aud = ttk.Button(
            aud_row,
            text=t('gui_btn_audacity'),
            command=self._choose_audacity_exe,
            padding=[8, 4]
        )
        self.btn_browse_aud.pack(side=tk.LEFT)

        # Audacity 探測狀態小標籤
        self.lbl_aud_status = ttk.Label(self.grp_opts, text="", font=self.app.font_std)
        self.lbl_aud_status.pack(anchor=tk.W, pady=(2, 0))
        self._update_audacity_status_display()

        # ── 5. 步驟 4: 執行與進度群組 (Card 4: Action & Progress) ──
        self.action_frame = ttk.Frame(self.main_container)
        self.action_frame.pack(fill=tk.X, pady=(4, 8))

        self.btn_start = ttk.Button(
            self.action_frame,
            text=t('gui_btn_start'),
            style="BigPunch.TButton",
            command=self._start_punch
        )
        self.btn_start.pack(fill=tk.X, pady=(0, 6))

        self.prog_bar = ttk.Progressbar(
            self.action_frame,
            mode='determinate',
            variable=self.progress_var
        )
        self.prog_bar.pack(fill=tk.X, pady=(0, 4))

        self.lbl_status = ttk.Label(self.action_frame, textvariable=self.status_var)
        self.lbl_status.pack(anchor=tk.W)

        # ── 6. 即時處理日誌 (Card 5: Universal Live Console) ──
        self.console_widget = self.app.create_console_log(
            self.main_container,
            height=7,
            title=t('gui_log_title'),
            show_toolbar=True
        )

        gui_art = (
            "                     /PPPPPPP                                /hh      \n"
            "                    | PP__  PP                              | hh      \n"
            "  /aaaaaa  /uu   /uu| PP  \\ PP /uu   /uu /nnnnnnn   /ccccccc| hhhhhhh \n"
            " |____  aa| uu  | uu| PPPPPPP/| uu  | uu| nn__  nn /cc_____/| hh__  hh\n"
            "  /aaaaaaa| uu  | uu| PP____/ | uu  | uu| nn  \\ nn| cc      | hh  \\ hh\n"
            " /aa__  aa| uu  | uu| PP      | uu  | uu| nn  | nn| cc      | hh  | hh\n"
            "|  aaaaaaa|  uuuuuu/| PP      |  uuuuuu/| nn  | nn|  ccccccc| hh  | hh\n"
            " \\_______/ \\______/ |__/       \\______/ |__/  |__/ \\_______/|__/  |__/\n"
            "======================================================================\n"
            f"{t('slogan1')}\n"
            f"{t('slogan2')}\n"
            "----------------------------------------------------------------------\n"
        )
        self.console_widget.insert(tk.END, gui_art)

        # ── 7. 底部資訊列 (Footer Bar: Version & Studio Signature) ──
        sep_footer = ttk.Separator(self.main_container, orient=tk.HORIZONTAL)
        sep_footer.pack(fill=tk.X, pady=(6, 4))

        self.footer_frame = ttk.Frame(self.main_container)
        self.footer_frame.pack(fill=tk.X)

        self.lbl_footer_ver = ttk.Label(
            self.footer_frame,
            text=t('gui_footer_version'),
            style="Subtitle.TLabel"
        )
        self.lbl_footer_ver.pack(side=tk.LEFT)

        self.lbl_footer_studio = ttk.Label(
            self.footer_frame,
            text=t('gui_footer_studio'),
            font=self.app.font_bold
        )
        self.lbl_footer_studio.pack(side=tk.RIGHT)

    def _toggle_theme(self):
        self.app.toggle_theme()
        # Refresh custom button style with new accent
        palette = UniversalUI.get_palette(is_dark=self.app.is_dark, follow_system_accent=True)
        accent_color = palette.get("accent", "#007acc")
        self.app.root.style.configure(
            "BigPunch.TButton",
            font=self.app.font_bold,
            padding=[14, 8],
            background=accent_color,
            foreground="white"
        )

    def _on_language_changed(self, event=None):
        disp = self.lang_display_var.get()
        selected_code = self.display_to_code.get(disp, disp)
        if selected_code:
            i18n.set_language(selected_code)
            self.app.config.set("language", selected_code)
            self.retranslate_ui()
            self.app.show_toast(f"Language: {disp}", level="info")

    def retranslate_ui(self):
        """Dynamic live UI retranslation."""
        self.root.title(t('gui_title'))
        self.lbl_slogan1.config(text=t('slogan1'))
        self.lbl_slogan2.config(text=t('slogan2'))
        self.lbl_subtitle.config(text=t('subtitle'))
        self.btn_theme.config(text=t('gui_theme_btn'))

        self.grp_source.config(text=t('gui_source_group'))
        self.btn_src_folder.config(text=t('gui_btn_folder'))
        self.btn_src_archive.config(text=t('gui_btn_archive'))

        self.grp_dest.config(text=t('gui_dest_group'))
        self.btn_browse_dest.config(text=t('gui_btn_browse'))

        self.grp_opts.config(text=t('gui_opt_group'))
        self.rb_target_ardour.config(text=t('gui_target_ardour'))
        self.rb_target_aup.config(text=t('gui_target_aup'))
        self.rb_flac.config(text=t('gui_fmt_flac'))
        self.rb_wav.config(text=t('gui_fmt_wav'))
        self.chk_edit.config(text=t('gui_chk_edit'))
        self.lbl_aud_path.config(text=t('gui_lbl_audacity_path'))
        self.btn_browse_aud.config(text=t('gui_btn_audacity'))

        if hasattr(self, 'lbl_footer_ver'):
            self.lbl_footer_ver.config(text=t('gui_footer_version'))
            self.lbl_footer_studio.config(text=t('gui_footer_studio'))

        if not self.is_running:
            self.btn_start.config(text=t('gui_btn_start'))
            self.status_var.set(t('gui_status_ready'))

        self._update_audacity_status_display()

    def _update_audacity_status_display(self):
        path_str = self.audacity_path_var.get().strip()
        exe = find_audacity_exe(path_str if path_str else None)
        if exe and exe.is_file():
            self.lbl_aud_status.config(
                text=f"{t('gui_audacity_detected')} {exe.name} ({exe.parent})",
                foreground="#28a745" if not self.app.is_dark else "#98c379"
            )
        else:
            self.lbl_aud_status.config(
                text=t('gui_audacity_not_found'),
                foreground="#6c757d" if not self.app.is_dark else "#abb2bf"
            )

    def _on_edit_check_toggled(self):
        if self.edit_var.get():
            # If checked, ensure we have a valid Audacity path
            path_str = self.audacity_path_var.get().strip()
            exe = find_audacity_exe(path_str if path_str else None)
            if not exe:
                self.app.showwarning(
                    t('gui_title'),
                    t('gui_warn_no_audacity')
                )
                self._choose_audacity_exe()

    def _choose_audacity_exe(self):
        filetypes = [("Audacity Executable", "audacity.exe;Audacity.app;audacity"), ("All Files", "*.*")]
        chosen = filedialog.askopenfilename(
            title=t('gui_btn_audacity'),
            filetypes=filetypes,
            parent=self.root
        )
        if chosen and os.path.isfile(chosen):
            resolved = str(Path(chosen).resolve())
            self.audacity_path_var.set(resolved)
            self.app.config.set("audacity_path", resolved)
            self._update_audacity_status_display()
            self.app.show_toast(f"Audacity path set: {Path(chosen).name}", level="success")

    def _choose_folder(self):
        folder = filedialog.askdirectory(title=t('gui_btn_folder'), parent=self.root)
        if folder:
            resolved = str(Path(folder).resolve())
            self.source_var.set(resolved)
            self.app.config.set("last_source", resolved)
            if not self.output_var.get():
                auto_out = str(Path(folder).resolve().parent / f"{Path(folder).name}_slim")
                self.output_var.set(auto_out)
                self.app.config.set("last_output", auto_out)

    def _choose_archive(self):
        filetypes = [("7z / Zip Archive", "*.7z *.zip"), ("All Files", "*.*")]
        archive = filedialog.askopenfilename(title=t('gui_btn_archive'), filetypes=filetypes, parent=self.root)
        if archive:
            resolved = str(Path(archive).resolve())
            self.source_var.set(resolved)
            self.app.config.set("last_source", resolved)
            if not self.output_var.get():
                auto_out = str(Path(archive).resolve().parent / f"{Path(archive).stem}_slim")
                self.output_var.set(auto_out)
                self.app.config.set("last_output", auto_out)

    def _choose_dest(self):
        folder = filedialog.askdirectory(title=t('gui_btn_browse'), parent=self.root)
        if folder:
            resolved = str(Path(folder).resolve())
            self.output_var.set(resolved)
            self.app.config.set("last_output", resolved)

    def _log(self, message):
        def append():
            self.app.log_to_widget(self.console_widget, message)
        self.root.after(0, append)

    def _set_status(self, text):
        self.root.after(0, lambda: self.status_var.set(text))

    def _set_progress(self, current, total):
        def update():
            if total > 0:
                self.progress_var.set((current / total) * 100)
            else:
                self.progress_var.set(0.0)
        self.root.after(0, update)

    def _start_punch(self):
        if self.is_running:
            return

        src = self.source_var.get().strip()
        out = self.output_var.get().strip()
        if not src or not os.path.exists(src):
            self.app.showwarning("auPunch", t('gui_err_no_source'))
            return
        if not out:
            self.app.showwarning("auPunch", t('gui_err_no_dest'))
            return

        # Save config state
        self.app.config.set("last_source", src)
        self.app.config.set("last_output", out)
        self.app.config.set("format", self.format_var.get())
        self.app.config.set("target", self.target_var.get())
        self.app.config.set("auto_open", self.edit_var.get())
        self.app.config.save()

        self.is_running = True
        self.btn_start.config(text=t('gui_btn_running'), state=tk.DISABLED)
        self.progress_var.set(0.0)

        # Background worker thread
        threading.Thread(target=self._worker, args=(src, out), daemon=True).start()

    def _worker(self, src_path, out_path):
        from auPunch import AuPunchRunner
        use_wav = (self.format_var.get() == "wav")
        target_mode = self.target_var.get()
        runner = AuPunchRunner(src_path, out_path, use_wav=use_wav, target=target_mode)
        
        projects = runner.scan_sources()
        total = len(projects)
        target_title = "Ardour DAW 會話 (.ardour)" if target_mode == "ardour" else "Audacity 2.4.2++ (.aup)"
        self._log(f"[*] 找到 {total} 個專案，開始抽脂處理 (目標格式: {target_title})...")

        for idx, p in enumerate(projects, 1):
            base_name = p['base_name']
            self._set_status(t('gui_status_processing', current=idx, total=total, name=base_name))
            self._set_progress(idx - 1, total)

            # Check resume
            proj_out_dir = Path(out_path) / base_name
            if target_mode == "ardour":
                target_file = proj_out_dir / f"{base_name}.ardour"
                target_media = proj_out_dir / "interchange" / base_name / "audiofiles"
            else:
                target_file = proj_out_dir / f"{base_name}.aup"
                target_media = proj_out_dir / "media"

            if target_file.exists() and target_media.exists() and any(target_media.iterdir()):
                self._log(t('gui_status_skipped', current=idx, total=total, name=base_name))
                continue

            try:
                # Handle single conversion
                if p['type'] == 'local':
                    res = runner.converter.convert(p['path'], out_path, use_wav=use_wav, target=target_mode)
                else:
                    # Archive single extraction
                    clean_f = runner.scratch_dir / f"{base_name}.aup3"
                    if clean_f.exists(): clean_f.unlink()
                    import subprocess
                    subprocess.run(
                        [runner.seven_zip, "e", "-sccUTF-8", str(runner.source_path), f"-o{runner.scratch_dir}", p['archive_name'], "-y"],
                        capture_output=True
                    )
                    ext_f = list(runner.scratch_dir.glob("*.aup3"))[0]
                    res = runner.converter.convert(ext_f, out_path, use_wav=use_wav, target=target_mode)
                    for f in runner.scratch_dir.glob("*"):
                        try: f.unlink()
                        except Exception: pass

                saved_mb = res['saved_size'] / (1024 * 1024)
                self._log(f"[{idx:03d}/{total:03d}] 瘦身成功: {base_name} (-{res['saved_percent']}%, 節省 {saved_mb:.1f} MB)")
            except Exception as e:
                self._log(f"[{idx:03d}/{total:03d}] [!] 失敗: {base_name} ({e})")

        self._set_progress(total, total)
        self._set_status(t('gui_complete_msg'))
        self._log(f"\n{t('gui_complete_msg')} 輸出目錄: {out_path}\n")

        # Open in Audacity or Explorer if requested
        if self.edit_var.get():
            if target_mode == "ardour":
                self._log(f"[*] 正在開啟成果目錄: {out_path} ...")
                try:
                    os.startfile(out_path)
                except Exception:
                    pass
            else:
                aup_files = list(Path(out_path).glob("**/*.aup"))
                if aup_files:
                    target_aup = aup_files[0]
                    custom_aud = self.audacity_path_var.get().strip() or None
                    self._log(f"[*] 正在以前台視窗開啟 Audacity: {target_aup.name} ...")
                    launched = launch_audacity(target_aup, custom_exe=custom_aud)
                    if not launched:
                        self._log("[!] 無法啟動 Audacity，請確認執行檔路徑是否正確。")

        def finish():
            self.btn_start.config(text=t('gui_btn_start'), state=tk.NORMAL)
            self.is_running = False
            self.app.show_toast(t('gui_complete_msg'), level="success")
            self.app.showinfo("auPunch", t('gui_complete_msg'))

        self.root.after(0, finish)

def launch_gui(source="", output=""):
    """
    Standard entry point to launch the auPunch UniversalUI GUI.
    """
    root = tk.Tk()
    default_dir = r"C:\_Suno\Old_Suno\audacity project"
    default_out = r"C:\_Suno\Old_Suno\audacity_projects_slim"
    
    init_src = source or (default_dir if os.path.exists(default_dir) else "")
    init_out = output or (default_out if os.path.exists(Path(default_out).parent) else "")

    app_wrapper = UniversalUI.UniversalApp(
        root,
        get_text("gui_title"),
        "aupunch_app",
        defaults={
            "geometry": "840x760",
            "ui_scale": 1.0,
            "format": "flac",
            "target": "ardour",
            "auto_open": False,
            "audacity_path": ""
        }
    )
    gui = AuPunchGUI(app_wrapper, default_source=init_src, default_output=init_out)
    root.mainloop()

if __name__ == '__main__':
    launch_gui()

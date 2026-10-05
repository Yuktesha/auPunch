# 🥊 auPunch

```text
“Punch your Audacity 3.x projects down to 2.4.2 & FLAC with zero hassle.”
======================================================================
                     /PPPPPPP                                /hh      
                    | PP__  PP                              | hh      
  /aaaaaa  /uu   /uu| PP  \ PP /uu   /uu /nnnnnnn   /ccccccc| hhhhhhh 
 |____  aa| uu  | uu| PPPPPPP/| uu  | uu| nn__  nn /cc_____/| hh__  hh
  /aaaaaaa| uu  | uu| PP____/ | uu  | uu| nn  \ nn| cc      | hh  \ hh
 /aa__  aa| uu  | uu| PP      | uu  | uu| nn  | nn| cc      | hh  | hh
|  aaaaaaa|  uuuuuu/| PP      |  uuuuuu/| nn  | nn|  ccccccc| hh  | hh
 \_______/ \______/ |__/       \______/ |__/  |__/ \_______/|__/  |__/
======================================================================
“auPunch: Heavyweight project conversion, lightweight files.”
```

<div align="center">

[![Python](https://img.shields.io/badge/Python-3.8%2B-3776AB.svg?logo=python&logoColor=white)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Platform](https://img.shields.io/badge/Platform-Windows%20%7C%20macOS%20%7C%20Linux-lightgrey.svg)]()
[![Studio](https://img.shields.io/badge/Studio-A%20Solid%20GUI%20Studio%20X%20MVlab-blueviolet.svg)]()

**一拳重擊 SQLite 肥胖怪獸，一鍵回歸 2.4.2 輕快殿堂！**  
*Knock out SQLite project bloat. Keep pure lossless sound.*

🌐 **Language / 語言切換**:  
[**繁體中文 (Traditional Chinese)**](#-繁體中文-traditional-chinese) | [**English**](#-english)

</div>

---

> ### 💡 研發哲學 (Core Philosophy)
> 
> **「軟體有時候所謂最新版不見得更好更穩定，削足適履往往適得其反，本工具因此孕育而生。」**  
> *"The latest version of software is not always the best or most stable. Forcing users to adapt to counterproductive architectural bloat is like cutting feet to fit shoes — auPunch was born to restore freedom, agility, and peace of mind."*

---

# 🇹🇼 繁體中文 (Traditional Chinese)

## 📖 痛點與緣起

自 Audacity 3.0 起，官方將專案改採單一 SQLite 資料庫格式（`.aup3`）。這項變更帶來了巨大的副作用：
- 專案體積急遽膨脹，數百 MB 的音軌往往膨脹成數 GB 甚至幾十 GB 的資料庫黑洞。
- 專案檔讀寫負擔巨大、編輯卡頓，甚至經常遭遇 SQLite WAL 損毀導致專案無法修復。
- 雲端同步與備份負擔沉重，原本純粹輕盈的音訊工作站淪為笨拙的資料庫怪獸。

**軟體所謂最新版不見得更好更穩定，削足適履往往適得其反！**  
**auPunch** 能將臃腫的 `.aup3` 資料庫無損還原為經典輕巧的 **Audacity 2.4.2++ 架構**（`.aup` 專案檔 ＋ `media/` 外部音訊目錄），預設調用無損最高等級 FLAC 壓縮，**實測平均體積大砍 70% ~ 96.5%**！

### 📊 實測瘦身成效 (Real-World Benchmarks)
- **單一專案實測**：1.2 GB 膨脹 `.aup3` ➔ **42 MB** 輕快專案（**-96.5%** 體積削減）。
- **大量專案批次實測**：共 127 個專案、原始總量 **77.21 GB** ➔ 抽脂後僅剩 **9.90 GB**（**淨省 67.31 GB，整體瘦身率達 -87.2%**）！

### 🥚 命名的雙重隱喻彩蛋 (Name Origin: aup undo rich)

「**auPunch**」看似是直覺強悍的「重拳抽脂（Punch）」，但背後其實隱藏著一段絕妙的文字學密碼：

$$\textbf{aup} + \textbf{un}\text{(do) }\textbf{ch}\text{(from rich)} \implies \textbf{auPunch}$$
$$(\text{亦即 } \textbf{aup undo rich} \text{ / } \textbf{aup un-rich})$$

Audacity 3.x 強塞的 SQLite 資料庫美其名讓專案變「豐富完整（Rich）」，實則帶來了動輒數 GB 的沉重肥胖枷鎖。**auPunch** 的初心正是 **「aup undo rich」** —— 逆轉過度封裝的虛胖架構、替專案徹底去油解膩，以極具衝擊力的一記重拳（Punch），重拾創作應有的輕快純粹！

---

## 🌟 核心特色

1. **⚡ 無損極限瘦身（Lossless FLAC by Default）**：
   - 預設自動提取音軌並調用 FFmpeg 壓為最高品質無損 **FLAC**，位元級 100% 零減損，體積削減 70%~96%。
   - 亦支援 `--wav` 參數，輸出標準未壓縮 WAV 音訊（最大相容模式）。
2. **🔄 串流滾動抽脂（Zero-Bloat Rolling Pipeline）**：
   - 支援直接讀取 `.7z` / `.zip` 壓縮封包（即使高達數十 GB），採用**單檔解壓 ➔ 抽脂轉檔 ➔ 銷毀暫存**之滾動流水線，全程硬碟額外開銷永遠只有 1~2 GB，小容量 SSD 也能無壓力批次處理！
3. **🖥️ UniversalUI 現代桌面介面（Modern Desktop GUI）**：
   - 遵循 `ATGprjs` 與 `rud()` 空間自適應排版第一原理。
   - 支援 Windows DWM 沉浸式暗色/淺色標題列、`Ctrl+T` 即時切換深淺色主題、動態字體與高 DPI 自適應。
   - 內建直觀的多語言切換（`zh_TW` 臺灣正體、`en_US` 美式英語、`zh_CN` 大陸簡體、`ja_JP` 日本語）。
   - 內建專屬 Consolas 終端機日誌視窗（含匯出與清空工具列）。
4. **🔍 智慧 Audacity 探測與前台連動（Smart Dispatcher）**：
   - 自動探測系統已安裝之 Audacity（Program Files, LocalAppData, PATH, Registry）或伴隨的可攜版（`AudacityPortable\audacity.exe`），亦可在 GUI 中隨選指定路徑。
   - 轉檔完成後可自動以前台視窗喚起 Audacity 載入專案進行剪輯。
5. **🎛️ 多軌獨立片段萃取與 3.x 智慧手柄保留（Multi-Clip & Smart Clips Preservation）**：
   - 徹底告別單一混音音檔的粗糙做法，優先將多軌工程中各個獨立 Clip 萃取為專屬的無損 FLAC，純淨隔離、軌道獨立。
   - 在專案 XML 中嚴格保留 Audacity 3.x 智慧手柄屬性（`trimLeft` 與 `trimRight`）。以 **Audacity 3.x** 開啟時即時還原非破壞性裁剪手柄，任意拖曳展開邊界；以 **Audacity 2.4.2** 開啟時無縫相容，享受「2.x 存檔極致小巧 ＋ 3.x 剪輯現代 DAW」的終極體驗！
6. **🎯 檔案總管右鍵選單整合（Context Menu Integration）**：
   - 提供 `關聯選單設定.ps1`，免管理員提權即可在 Windows 檔案總管右鍵加入「🥊 使用 auPunch 輕快開啟」。
   - 點擊 `.aup`（2.x）➔ 秒開 Audacity！
   - 點擊 `.aup3`（3.x）➔ 自動極速抽脂為 2.4.2++ 後秒開專案！

---

## 🚀 快速上手 (Quick Start)

### 依賴環境
- **Python 3.8+**
- **FFmpeg**（需加入系統 PATH）
- **7-Zip**（可選，若需串流讀取 `.7z` 封包）

### 1. 啟動圖形化介面 (GUI Mode)
```powershell
python auPunch.py --gui
# 或透過原生 PowerShell 進入點：
.\auPunch.ps1 -GUI
```

### 2. 命令列模式 (CLI Mode)
```powershell
# 基本用法（無參數等同 --help）
python auPunch.py

# 批次抽脂資料夾內所有專案（預設 FLAC 極限瘦身）
python auPunch.py --source "C:\MyProjects" --output "C:\MyProjects_slim"

# 串流滾動抽脂 7z 壓縮檔（免預先解壓縮）
python auPunch.py --source "C:\audacity_projects.7z" --output "C:\slim_out"

# 指定輸出未壓縮 WAV（相容性模式）
python auPunch.py --source "C:\MyProjects" --output "C:\MyProjects_wav" --wav

# 抽脂完成後自動以 Audacity 開啟專案
python auPunch.py --source "C:\MyProjects" --edit
```

### 3. CLI 參數一覽表
| 參數 | 簡寫 | 說明 |
| :--- | :--- | :--- |
| `--source <path>` | `-s` | 來源路徑（支援 `.7z` 壓縮檔或包含 `.aup3` 的資料夾） |
| `--output <dir>` | `-o` | 輸出目錄（轉檔後專案存放位置） |
| `--wav` | | 指定輸出標準未壓縮 WAV（預設為無損高效 FLAC） |
| `--limit <N>` | | 限制模式：僅處理前 N 個專案（測試用） |
| `--edit` | | 轉換完成後自動以 Audacity 前台開啟專案 |
| `--gui` | `-g`, `-G` | 啟動圖形化使用者介面 (UniversalUI GUI) |
| `--help` | `-h`, `--?` | 顯示說明訊息並退出 |

---

# 🇺🇸 English

## 📖 The Core Problem & Motivation

Starting from Audacity 3.0, the project format transitioned to a monolithic SQLite database (`.aup3`). While conceptually neat, this architectural decision introduced severe real-world problems:
- **Catastrophic Project Bloat**: Modest audio sessions of a few hundred megabytes swell into multi-gigabyte monolithic databases.
- **Sluggish Performance & High Failure Rates**: Massive I/O overhead leads to stuttering and frequent SQLite WAL corruption, often resulting in unrecoverable project loss.
- **Storage & Backup Headaches**: Cloud syncing and archival backup become excruciatingly slow and expensive.

**"The latest version of software is not always the best or most stable. Forcing users to adapt to counterproductive bloat is like cutting feet to fit shoes — auPunch was born out of this conviction."**

**auPunch** dissects bloated `.aup3` database projects, restores them into the lightweight and robust **Audacity 2.4.2++ architecture** (`.aup` project XML + referenced `media/` folder), and compresses tracks using bit-perfect lossless **FLAC** by default — slashing disk usage by **70% to 96.5%**!

### 📊 Benchmark Results
- **Single Project**: 1.2 GB `.aup3` ➔ **42 MB** slim project (**-96.5%** reduction).
- **Batch Processing**: 127 projects totaling **77.21 GB** ➔ slimmed down to **9.90 GB** (**saved 67.31 GB, -87.2% overall space saved**)!

### 🥚 The Hidden Metaphor: "aup undo rich"

While **auPunch** immediately conveys a heavyweight knockout punch delivered to bloated databases, the name holds a brilliant linguistic Easter egg:

$$\textbf{aup} + \textbf{un}\text{(do) }\textbf{ch}\text{(from rich)} \implies \textbf{auPunch}$$
$$(\text{or } \textbf{aup undo rich} \text{ / } \textbf{aup un-rich})$$

Audacity 3.x's SQLite monolithic database was marketed as making projects "richer", but in reality, it burdened creators with multi-gigabyte bloat and fragile I/O overhead. **auPunch** literally originated from the philosophy of **"aup undo rich"** — undoing the over-engineered bloat, un-riching the excessive overhead, and delivering freedom back to the user with a single decisive punch!

---

## 🌟 Key Features

1. **⚡ Extreme Lossless Slimming (FLAC by Default)**:
   - Uses FFmpeg to extract audio tracks into highest-compression, bit-perfect **FLAC**, preserving 100% audio fidelity while shrinking sizes by 70%~96%.
   - Supports uncompressed `--wav` output when maximum legacy compatibility is required.
2. **🔄 Zero-Disk-Bloat Rolling Pipeline**:
   - Stream-processes `.7z` / `.zip` multi-gigabyte archives: **extract single project ➔ convert & compress ➔ destroy scratch files**. Total temporary disk usage never exceeds 1~2 GB!
3. **🖥️ UniversalUI Modern Desktop GUI**:
   - Engineered under `ATGprjs` and `rud()` adaptive spatial geometry standards.
   - Features Windows DWM immersive titlebar, instant `Ctrl+T` dark/light theme switching, dynamic typography, and high-DPI scaling.
   - Multi-language matrix (`zh_TW`, `en_US`, `zh_CN`, `ja_JP`) with instant live retranslation.
   - Built-in Consolas terminal-style Live Console with log export and clear capabilities.
4. **🔍 Smart Audacity Dispatcher**:
   - Automatically discovers local Audacity installations (`Program Files`, `LocalAppData`, `PATH`, Registry) or bundled companion portable versions (`AudacityPortable\audacity.exe`), with full manual path override in GUI.
   - Seamlessly launches the converted project in Audacity after processing.
5. **🎛️ Multi-Clip Isolation & 3.x Smart Clips Preservation**:
   - Replaces coarse single-mixdown flattening with granular multi-clip extraction, preserving track independence across complex arrangements.
   - Strictly preserves Audacity 3.x Smart Clip trimming metadata (`trimLeft` and `trimRight`). Opening the project in **Audacity 3.x** immediately restores non-destructive trimming handles on each clip, while opening in **Audacity 2.4.2** functions smoothly with bit-perfect audio waveforms — delivering the ultimate hybrid workflow: 2.x ultra-compact storage + 3.x modern DAW editing flexibility!
6. **🎯 Windows Explorer Context Menu**:
   - Provides `關聯選單設定.ps1` to register right-click shortcuts without needing Administrator UAC elevation.
   - Click `.aup` (2.x) ➔ Opens Audacity instantly!
   - Click `.aup3` (3.x) ➔ Fast background slimming and immediate launch!

---

## 🚀 Quick Start (English)

### Prerequisites
- **Python 3.8+**
- **FFmpeg** (must be available in system `PATH`)
- **7-Zip** (optional, for streaming directly from `.7z` archives)

### 1. Launch GUI Mode
```powershell
python auPunch.py --gui
# Or via native PowerShell script:
.\auPunch.ps1 -GUI
```

### 2. Command-Line Mode (CLI)
```powershell
# Show help (running with no arguments defaults to help)
python auPunch.py

# Batch convert all projects in a directory (default FLAC extreme slimming)
python auPunch.py --source "C:\MyProjects" --output "C:\MyProjects_slim"

# Stream-convert projects directly from 7z archive (no pre-extraction required)
python auPunch.py --source "C:\audacity_projects.7z" --output "C:\slim_out"

# Convert with uncompressed WAV (legacy compatibility mode)
python auPunch.py --source "C:\MyProjects" --output "C:\MyProjects_wav" --wav

# Convert and immediately open in Audacity for editing
python auPunch.py --source "C:\MyProjects" --edit
```

### 3. CLI Command Options
| Option | Short | Description |
| :--- | :--- | :--- |
| `--source <path>` | `-s` | Source path (.7z archive or folder containing `.aup3` files) |
| `--output <dir>` | `-o` | Destination directory for converted slim projects |
| `--wav` | | Output uncompressed standard WAV instead of default FLAC |
| `--limit <N>` | | Limit processing to first N projects (for testing) |
| `--edit` | | Auto-open converted project in Audacity when finished |
| `--gui` | `-g`, `-G` | Launch Graphical User Interface (UniversalUI) |
| `--help` | `-h`, `--?` | Display help information and exit |

---

## 📁 專案架構 (Project Structure)

```text
auPunch/
├── auPunch.py            # CLI entry point & batch conversion orchestrator
├── gui.py                # UniversalUI desktop application
├── aup3_converter.py     # SQLite .aup3 deconstruction & 2.4.2++ assembly engine
├── auPunchLauncher.py    # Smart Audacity dispatcher (.aup / .aup3)
├── AupPackager.py        # 2.4.2 project consolidator & external media packager
├── i18n.py               # Multi-language bridge module
├── _lang/
│   └── languages.tsv     # Tab-separated multi-language matrix (zh_TW, en_US, zh_CN, ja_JP)
├── _lib/                 # UniversalUI self-contained core runtime library
├── tools/                # audacity-project-tools helper binary
├── auPunch.ps1           # UTF-8 BOM PowerShell CLI wrapper
├── auPunchLauncher.ps1   # Dispatcher PowerShell wrapper
├── AupPackager.ps1       # Packager PowerShell wrapper
├── 關聯選單設定.ps1      # Context menu registration script
├── LICENSE               # MIT License
└── README.md             # Project documentation (Bilingual)
```

---

## ⚖️ 第三方聲明 (Disclaimer)

- **Audacity®** is a registered trademark of Muse Group and the Audacity Team, licensed under the GNU General Public License (GPL).
- **auPunch** is an independent, open-source utility and is not affiliated with, endorsed by, or sponsored by Audacity or Muse Group.
- All conversions are non-destructive to your original source files.

---

## 📄 授權條款 (License)

This project is licensed under the **[MIT License](LICENSE)**.

----------------------------------------------------------------------
**A Solid GUI Studio X MVlab**

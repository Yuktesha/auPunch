# 🥊 auPunch

```text
“Punch your Audacity 3.x projects down to Native Ardour DAW & FLAC with zero hassle.”
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

**一拳重擊 SQLite 肥胖怪獸，一鍵直達 Ardour 專業 DAW 世界！**  
*Knock out SQLite project bloat. Convert directly to Native Ardour DAW sessions!*

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

自 Audacity 3.0 被商業收購以來，專案改採單一 SQLite 資料庫格式（`.aup3`），並在架構上引發諸多困擾：
- **專案體積急遽膨脹**：數百 MB 的音軌往往膨脹成數 GB 甚至幾十 GB 的資料庫黑洞。
- **讀寫負擔巨大、容易損毀**：大量 I/O 導致編輯卡頓，且頻繁發生 SQLite WAL 損毀導致專案無法開啟。
- **路徑解析缺陷與歷史包袱**：舊版 `.aup` 格式在新環境中若非在特定路徑開啟極易遺失路徑，甚至出現音訊遺失現象。

**與其在歷史包袱中削足適履，不如直接擁抱世界級專業開源數位音訊工作站（DAW）—— Ardour！**  
**auPunch** 能將臃腫的 `.aup3` 資料庫無損還原並轉檔為標準 **Ardour DAW 工程會話（`.ardour`）**，預設調用無損最高等級 FLAC 壓縮，**實測平均體積大砍 70% ~ 96.5%**！

### 📊 實測瘦身與轉檔成效 (Real-World Benchmarks)
- **單一專案實測（110 Bababa.aup3）**：221 MB ➔ **41.7 MB** Ardour 會話（**-81.19%**，2 組立體聲軌道，14 個片段，轉檔耗時僅 3 秒）。
- **大型 30 軌專案實測（兄弟節.aup3）**：1.38 GB ➔ **185.7 MB** Ardour 會話（**-86.64%**，15 組原生立體聲軌道，32 個片段，轉檔耗時僅 9.8 秒）。
- **大量專案批次實測**：共 127 個專案、原始總量 **77.21 GB** ➔ 抽脂後僅剩 **9.90 GB**（**淨省 67.31 GB，整體瘦身率達 -87.2%**）！

### 🥚 命名的雙重隱喻彩蛋 (Name Origin: aup undo rich)

「**auPunch**」看似是直覺強悍的「重拳抽脂（Punch）」，但背後其實隱藏著一段絕妙的文字學密碼：

$$\textbf{aup} + \textbf{un}\text{(do) }\textbf{ch}\text{(from rich)} \implies \textbf{auPunch}$$
$$(\text{亦即 } \textbf{aup undo rich} \text{ / } \textbf{aup un-rich})$$

Audacity 3.x 強塞的 SQLite 資料庫美其名讓專案變「豐富完整（Rich）」，實則帶來了動輒數 GB 的沉重肥胖枷鎖。**auPunch** 的初心正是 **「aup undo rich」** —— 逆轉過度封裝的虛胖架構、替專案徹底去油解膩，以極具衝擊力的一記重拳（Punch），直通專業 DAW 的廣闊殿堂！

---

## 🌟 核心特色

1. **🎛️ 直出原生 Ardour 專業 DAW 會話工程（Native Ardour Session by Default）**：
   - 預設產生標準 Ardour 工程結構：`<ProjectName>/<ProjectName>.ardour` 與 `interchange/<ProjectName>/audiofiles/*.flac`。
   - 啟動 Ardour 即可直接開箱即用，無需手動重新連結音檔。
2. **🎧 智慧立體聲對軌識別與合併（Smart Stereo Pair Recombination）**：
   - Audacity 會將雙聲道立體聲拆為兩個獨立的單聲道軌道（`channel="0"` 與 `channel="1"`）。
   - auPunch 自動識別成對軌道，調用 FFmpeg `amerge` 合併為原生雙聲道無損 FLAC。音軌數與檔案數減半，並藉助 FLAC Mid-Side 立體聲壓縮技術額外再減省 20%~30% 磁碟空間！
3. **⏱️ 樣本級精準時間軸對齊（Sample-Accurate Timeline Math）**：
   - 深入 Audacity 3.x 幾何修剪數學，以公式 `pos_samples = int(round((offset + trimLeft) * sample_rate))` 進行微秒/樣本級精準對位。
   - 徹底保留非破壞性裁剪手柄，零爆音、零相位差、零時間漂移。
4. **📈 音量包絡線與自動化曲線轉移（Automation & Envelope Preservation）**：
   - 自動將 Audacity `<envelope>` 四點式音量控制點轉換為 Ardour 原生 `<AutomationList>` 音量自動化事件，完整保留淡入（Fade-In）、淡出（Fade-Out）與動態音量調控。
5. **⚡ 無損極限瘦身（Lossless FLAC by Default）**：
   - 預設自動提取音軌並調用 FFmpeg 壓為最高品質無損 **FLAC**，位元級 100% 零減損，體積削減 70%~96%。
   - 亦支援 `--wav` 參數，輸出標準未壓縮 WAV 音訊。
6. **🔄 串流滾動抽脂（Zero-Bloat Rolling Pipeline）**：
   - 支援直接讀取 `.7z` / `.zip` 壓縮封包（即使高達數十 GB），採用**單檔解壓 ➔ 抽脂轉檔 ➔ 銷毀暫存**之滾動流水線，全程硬碟額外開銷永遠只有 1~2 GB，小容量 SSD 也能無壓力批次處理！
7. **🖥️ UniversalUI 現代桌面介面（Modern Desktop GUI）**：
   - 遵循 `ATGprjs` 與 `rud()` 空間自適應排版第一原理。
   - 支援 Windows DWM 沉浸式暗色/淺色標題列、`Ctrl+T` 即時切換深淺色主題、動態字體與高 DPI 自適應。
   - 內建四國語言切換（`zh_TW` 臺灣正體、`en_US` 美式英語、`zh_CN` 大陸簡體、`ja_JP` 日本語）。
   - 內建專屬 Consolas 終端機日誌視窗（含匯出與清空工具列）。
8. **🔙 舊版 Audacity 相容模式（Legacy Compatibility Mode）**：
   - 透過 `--target aup` 可選擇轉為 Audacity 2.4.2++ 架構（`.aup` 專案檔 ＋ `media/` 音訊目錄）。

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

# 批次抽脂資料夾內所有專案為 Ardour 會話（預設 FLAC 極限瘦身）
python auPunch.py --source "C:\MyProjects" --output "C:\MyProjects_slim"

# 串流滾動抽脂 7z 壓縮檔為 Ardour 會話（免預先解壓縮，零硬碟膨脹壓力）
python auPunch.py --source "C:\audacity_projects.7z" --output "C:\slim_out"

# 指定輸出未壓縮 WAV（最大相容模式）
python auPunch.py --source "C:\MyProjects" --output "C:\MyProjects_wav" --wav

# 抽脂為舊版 Audacity 相容格式 (.aup)
python auPunch.py --source "C:\MyProjects" --output "C:\MyProjects_aup" --target aup

# 轉換完成後自動開啟成果目錄
python auPunch.py --source "C:\MyProjects" --edit
```

### 3. CLI 參數一覽表
| 參數 | 簡寫 | 說明 |
| :--- | :--- | :--- |
| `--source <path>` | `-s` | 來源路徑（支援 `.7z` 壓縮檔、單一 `.aup3` 或包含 `.aup3` 的資料夾） |
| `--output <dir>` | `-o` | 輸出目錄（轉檔後專案存放位置） |
| `--target <format>` | `-t` | 目標 DAW 格式：`ardour`（預設，直出原生 Ardour 會話）或 `aup`（舊版 Audacity 相容） |
| `--wav` | | 指定輸出標準未壓縮 WAV（預設為無損高效 FLAC） |
| `--limit <N>` | | 限制模式：僅處理前 N 個專案（測試用） |
| `--edit` | | 轉換完成後自動開啟專案成果（自動探測 DAW 或開啟目錄） |
| `--gui` | `-g`, `-G` | 啟動圖形化使用者介面 (UniversalUI GUI) |
| `--help` | `-h`, `--?` | 顯示說明訊息並退出 |

---

# 🇺🇸 English

## 📖 The Core Problem & Motivation

Since Audacity 3.0 was acquired commercially, projects shifted to a single monolithic SQLite database format (`.aup3`). While conceptually neat, this architectural decision introduced severe issues:
- **Catastrophic Project Bloat**: Modest audio sessions of a few hundred megabytes swell into multi-gigabyte monolithic databases.
- **Sluggish Performance & High Failure Rates**: Massive I/O overhead leads to stuttering and frequent SQLite WAL corruption, often resulting in unrecoverable project loss.
- **Path Fragility in Legacy Formats**: Old `.aup` XML format easily loses referenced audio blocks when executed from outside the session directory.

**Rather than cutting feet to fit the shoes of legacy software, leap forward into the world-class open-source Digital Audio Workstation — Ardour!**  
**auPunch** deconstructs bloated `.aup3` database projects and converts them directly into native **Ardour DAW Sessions (`.ardour`)** with bit-perfect lossless **FLAC** audio stems — slashing disk usage by **70% to 96.5%**!

### 📊 Benchmark Results
- **Single Project (110 Bababa.aup3)**: 221 MB ➔ **41.7 MB** Ardour session (**-81.19%** reduction, 2 stereo tracks, 14 clips, finished in 3s).
- **Large 30-Track Project (兄弟節.aup3)**: 1.38 GB ➔ **185.7 MB** Ardour session (**-86.64%** reduction, 15 stereo tracks, 32 clips, finished in 9.8s).
- **Batch Processing**: 127 projects totaling **77.21 GB** ➔ slimmed down to **9.90 GB** (**saved 67.31 GB, -87.2% overall space saved**)!

### 🥚 The Hidden Metaphor: "aup undo rich"

While **auPunch** immediately conveys a heavyweight knockout punch delivered to bloated databases, the name holds a brilliant linguistic Easter egg:

$$\textbf{aup} + \textbf{un}\text{(do) }\textbf{ch}\text{(from rich)} \implies \textbf{auPunch}$$
$$(\text{or } \textbf{aup undo rich} \text{ / } \textbf{aup un-rich})$$

Audacity 3.x's SQLite monolithic database was marketed as making projects "richer", but in reality, it burdened creators with multi-gigabyte bloat and fragile I/O overhead. **auPunch** literally originated from the philosophy of **"aup undo rich"** — undoing the over-engineered bloat, un-riching the excessive overhead, and delivering freedom back to the user with a single decisive punch!

---

## 🌟 Key Features

1. **🎛️ Native Ardour DAW Session Generation by Default**:
   - Generates clean, standard Ardour session directory structures: `<ProjectName>/<ProjectName>.ardour` and `interchange/<ProjectName>/audiofiles/*.flac`.
   - Open directly in Ardour out of the box without any missing file prompts.
2. **🎧 Smart Stereo Pair Recombination**:
   - Audacity splits 2-channel stereo tracks into separate mono tracks (`channel="0"` and `channel="1"`).
   - auPunch automatically identifies paired tracks and merges them into unified 2-channel lossless stereo FLAC files using FFmpeg `amerge`. This halves the file count and gains an extra 20%~30% disk space reduction via FLAC Mid-Side Stereo compression!
3. **⏱️ Sample-Accurate Timeline Positioning**:
   - Accurately computes timeline clip positions down to the individual sample: `pos_samples = int(round((offset + trimLeft) * sample_rate))`.
   - Preserves non-destructive trimming handles with zero clicks, phase issues, or timing drift.
4. **📈 Envelope Automation Curve Conversion**:
   - Automatically translates Audacity `<envelope>` 4-point volume control nodes into native Ardour `<AutomationList>` volume gain events, preserving fades and dynamic volume curves.
5. **⚡ Extreme Lossless Slimming (FLAC by Default)**:
   - Uses FFmpeg to extract audio tracks into highest-compression, bit-perfect **FLAC**, preserving 100% audio fidelity while shrinking sizes by 70%~96%.
   - Supports uncompressed `--wav` output when maximum compatibility is required.
6. **🔄 Zero-Disk-Bloat Rolling Pipeline**:
   - Stream-processes `.7z` / `.zip` multi-gigabyte archives: **extract single project ➔ convert & compress ➔ destroy scratch files**. Total temporary disk usage never exceeds 1~2 GB!
7. **🖥️ UniversalUI Modern Desktop GUI**:
   - Engineered under `ATGprjs` and `rud()` adaptive spatial geometry standards.
   - Features Windows DWM immersive titlebar, instant `Ctrl+T` dark/light theme switching, dynamic typography, and high-DPI scaling.
   - Multi-language matrix (`zh_TW`, `en_US`, `zh_CN`, `ja_JP`) with instant live retranslation.
   - Built-in Consolas terminal-style Live Console with log export and clear capabilities.
8. **🔙 Legacy Audacity Compatibility Mode**:
   - Converts to Audacity 2.4.2++ (`.aup` + `media/`) via `--target aup`.

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
# Show help
python auPunch.py

# Batch convert all projects in a directory into Ardour sessions (default FLAC)
python auPunch.py --source "C:\MyProjects" --output "C:\MyProjects_slim"

# Stream-convert projects directly from 7z archive into Ardour sessions
python auPunch.py --source "C:\audacity_projects.7z" --output "C:\slim_out"

# Convert with uncompressed WAV
python auPunch.py --source "C:\MyProjects" --output "C:\MyProjects_wav" --wav

# Convert to legacy Audacity 2.4.2++ format
python auPunch.py --source "C:\MyProjects" --output "C:\MyProjects_aup" --target aup

# Convert and automatically open destination folder
python auPunch.py --source "C:\MyProjects" --edit
```

### 3. CLI Command Options
| Option | Short | Description |
| :--- | :--- | :--- |
| `--source <path>` | `-s` | Source path (.7z archive, single `.aup3`, or directory containing `.aup3` files) |
| `--output <dir>` | `-o` | Destination directory for converted slim projects |
| `--target <format>`| `-t` | Target DAW format: `ardour` (default, native Ardour session) or `aup` (legacy Audacity) |
| `--wav` | | Output uncompressed standard WAV instead of default FLAC |
| `--limit <N>` | | Limit processing to first N projects (for testing) |
| `--edit` | | Auto-open converted project or destination when finished |
| `--gui` | `-g`, `-G` | Launch Graphical User Interface (UniversalUI) |
| `--help` | `-h`, `--?` | Display help information and exit |

---

## 📁 專案架構 (Project Structure)

```text
auPunch/
├── auPunch.py            # CLI entry point & batch conversion orchestrator
├── gui.py                # UniversalUI desktop application
├── ardour_exporter.py    # Native Ardour DAW Session (.ardour) XML generator
├── aup3_converter.py     # SQLite .aup3 deconstruction & conversion engine
├── test_ardour_exporter.py # Unit tests for Ardour session generation
├── test_converter.py     # Unit tests for converter pipeline
├── auPunchLauncher.py    # Smart DAW & Audacity dispatcher
├── AupPackager.py        # Project consolidator & external media packager
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

- **Ardour®** is a registered trademark of Paul Davis and the Ardour Community, licensed under the GNU General Public License (GPL).
- **Audacity®** is a registered trademark of Muse Group and the Audacity Team, licensed under the GNU General Public License (GPL).
- **auPunch** is an independent, open-source utility and is not affiliated with, endorsed by, or sponsored by Ardour, Audacity, or Muse Group.
- All conversions are non-destructive to your original source files.

---

## 📄 授權條款 (License)

This project is licensed under the **[MIT License](LICENSE)**.

----------------------------------------------------------------------
**A Solid GUI Studio X MVlab**

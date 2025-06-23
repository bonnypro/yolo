# AI 蒙皮铝屑观察助手

**AI 蒙皮铝屑观察助手**是一款基于 YOLOv8 深度学习模型的高性能目标检测应用。它旨在为工业生产线等场景提供实时、精准的视频监控分析，并通过先进的感兴趣区域 (ROI) 管理功能，帮助用户聚焦关键区域，提升检测效率与准确性。

## ✨ 核心功能

- **高性能目标检测**: 集成 YOLOv8 模型，提供快速、精准的实时对象识别。
- **高级 ROI 管理**:
  - **可视化绘制**: 通过鼠标交互，轻松在视频上绘制任意形状的多边形 ROI。
  - **多配置支持**: 创建、保存、切换和管理多个独立的 ROI 配置。
  - **精准坐标**: 坐标系统经过校准，确保不受窗口缩放影响，定位精确。
  - **持久化存储**: 所有 ROI 配置自动保存在 `roi_configs` 文件夹中，重启后无缝加载。
- **多种视频源**: 支持从 USB 摄像头或本地视频文件读取视频流。
- **视频录制**: 支持将处理后的视频流（包含检测框）录制并保存为文件。
- **高度可配置**: 通过独立的配置文件管理应用行为和界面样式。
- **简洁的用户界面**: 使用 PyQt6 构建，提供直观、易于操作的图形界面。

---

## 🚀 快速上手

### 1. 环境配置

本项目依赖于 Conda 环境。请确保您的环境中已安装必要的库。

```bash
# 安装依赖
pip install -r requirements.txt

# 如果遇到QT相关错误 (如 xcb)，请尝试安装以下库
sudo apt-get update
sudo apt-get install libxcb-cursor0
```

### 2. 运行程序

```bash
python main.py
```

---

## 📖 使用指南

### 主界面概览

应用主窗口分为三个主要部分：
1.  **视频显示区 (中央)**: 显示来自摄像头或视频文件的实时画面、检测结果以及 ROI 区域。
2.  **功能面板 (左侧)**: 控制模型加载、视频源选择、检测启停以及进入 ROI 设置模式。
3.  **ROI 控制面板 (底部)**: 在进入 ROI 管理模式后出现，用于创建、编辑和管理所有 ROI 配置。

### 基本操作流程

1.  **加载模型**: 点击左侧面板的 `加载模型` 按钮，选择一个 `.pt` 格式的 YOLOv8 模型文件。
2.  **选择视频源**:
    - 点击 `打开摄像头` 使用默认的 USB 摄像头。
    - 点击 `打开视频文件` 选择一个本地视频文件。
3.  **开始检测**: 点击 `开始检测` 按钮，模型将开始对视频流进行实时分析。再次点击可暂停。

### ROI 功能详解

ROI (Region of Interest) 功能允许您指定视频中的一个或多个区域进行重点分析，这可以极大地提升检测速度并减少无关区域的误报。

#### **如何创建和管理 ROI？**

**步骤一：进入 ROI 管理模式**

- 在左侧"功能面板"中，点击 **`设置ROI区域`** 按钮。
- 程序将进入 ROI 管理模式，视频下方的 **ROI 控制面板** 会随之出现。此时，目标检测会暂停，以便您进行 ROI 编辑。

**步骤二：创建新的 ROI**

1.  在 ROI 控制面板中，点击 **`创建新的ROI`** 按钮。
2.  系统会自动生成一个默认名称 (如 `ROI_1`)，您可以立即在"ROI名称"输入框中修改它。
3.  此时，您可以在视频画面上通过**鼠标左键点击**来添加 ROI 的顶点（最多100个）。
4.  当您定义完所有顶点后（至少3个），点击 **`保存ROI`** 按钮，新的 ROI 配置即被创建并保存。

**步骤三：编辑和使用 ROI**

1.  从"ROI选择"下拉菜单中，选择一个您想编辑或使用的 ROI。
2.  该 ROI 的边界和顶点会立即显示在视频上，其坐标会加载到下方的"坐标列表"中。
3.  您可以直接在**坐标文本框**中手动修改顶点的 `x,y` 值，修改会实时在视频上更新。修改完成后点击 `保存ROI`。
4.  要**在检测中使用 ROI**，只需勾选 **`启用ROI`** 复选框，并选择好要使用的 ROI。
5.  返回主界面，点击 `开始检测`，算法将仅对您选定的 ROI 区域进行分析。

#### **ROI 控制面板详解**

- **`启用ROI`** (复选框): 全局开关。勾选后，检测将应用选定的 ROI。
- **`ROI选择`** (下拉菜单): 列出所有已保存的 ROI 配置，用于切换、查看和编辑。
- **`ROI名称`** (文本输入框): 显示当前 ROI 的名称，允许您在创建或编辑时修改。
- **`坐标列表`** (滚动区域): 以 `[序号][x,y]` 的格式显示当前 ROI 的所有顶点坐标，并支持直接编辑。
- **`创建新的ROI`** (按钮): 启动新 ROI 的绘制流程。
- **`清除当前ROI`** (按钮): 删除当前在下拉菜单中选中的 ROI 配置。
- **`保存ROI`** (按钮): 保存当前正在创建或修改的 ROI。

---

## ⚙️ 配置文件

### `config.py`
此文件是应用的**配置中心**，集中管理所有配置、样式和常量，如应用标题、默认置信度、UI 样式等。修改此文件可以快速调整应用的基础行为和外观。

### `roi_configs/` 文件夹
此文件夹用于**持久化存储所有与ROI相关的数据**。

- **`roi_configs/roi_config.json`**: 存储全局ROI设置，如是否启用、当前激活的ROI名称。
- **`roi_configs/*.json`**: 每个 `.json` 文件代表一个独立的ROI配置，包含了其顶点坐标等信息。

**示例 `roi_configs/ROI_1.json` 格式:**
```json
{
  "name": "ROI_1",
  "points": [
    [100, 150],
    [200, 150],
    [200, 250],
    [100, 250]
  ],
  "created_time": "...",
  "last_used": "..."
}
```

---

## 🏗️ 技术架构概览

项目采用**分层解耦**的设计思想，将核心功能模块化，以保证代码的清晰度、可维护性和可扩展性。

- **`main.py`**: 程序主入口。
- **`config.py`**: 全局配置与样式中心。
- **`core/`**: 核心业务逻辑目录。
  - `model_handler.py`: 封装 YOLO 模型的加载与推理。
  - `video_handler.py`: 处理视频流的捕获、读取和录制。
  - `roi_handler.py`: 封装所有 ROI 相关的逻辑，包括绘制、坐标转换和文件操作。
- **`ui/`**: 用户界面目录。
  - `main_window.py`: 主窗口的布局和主要交互逻辑。
  - `roi_panel.py`: ROI 控制面板的 UI 和交互。

这种结构使得各部分职责单一，便于独立开发、测试和未来的功能扩展。

---

## 📝 更新日志

- **v1.2.0**
  - **新增**: "创建新的ROI"按钮，优化了 ROI 创建流程。
  - **新增**: ROI 顶点数量上限提升至 100，并添加了UI提示。
  - **优化**: "清除当前ROI"现在会同步清空界面上的坐标列表。
  - **优化**: 完善了 ROI 的编辑和保存逻辑，支持重命名。

- **v1.1.0**
  - **修复**: 彻底解决了鼠标点击与视频帧坐标的映射问题，实现了精准定位。
  - **修复**: ROI 区域外的图像在检测时保持原样显示，不再是黑屏。
  - **优化**: ROI 控制面板布局调整为左对齐，提升了视觉一致性。

- **v1.0.0**
  - **发布**: ROI 基础功能上线，支持绘制、保存和在检测中应用。




# 环境配置笔记（防丢）


## Conda Pack 环境迁移
### 安装 conda-pack。
conda install conda-pack 
或者
pip install conda-pack

### 查看服务器中已有的conda环境。
conda info -e

### 恢复 
假设已经将服务器A打包的环境拷贝到服务器B用户目录下/home/abc/env_name.tar.gz，服务器B的anaconda安装目录位于 /home/abc/anaconda3/，那么按照下面步骤进行操作：
命令 mkdir -p /home/abc/anaconda3/envs/环境名
tar -xzvf 环境名.tar.gz -C /home/abc/anaconda3/envs/环境名
查看所有环境
conda info -e
激活环境
conda activate 环境名
查看安装包
conda list

### 创建环境
conda create --name ultralytics-cuda-streamlit-qt-env python=3.11 qt -y
conda install -c pytorch -c nvidia -c conda-forge pytorch torchvision pytorch-cuda=11.8 ultralytics streamlit

### QT 错误

解决方法（需要安装 xcb-cursor0 库）：

终端内执行：
sudo apt-get update
sudo apt-get install libxcb-cursor0


### 另外的办法

如果有qt报警，则设置环境变量，把env里面的platforms目录复制到当前代码目录

export QT_QPA_PLATFORM_PLUGIN_PATH=./platforms

或者在程序里指定好以下配置
获取当前 Conda 环境的根目录
conda_env_path = Path(os.environ["CONDA_PREFIX"])
设置 QT_QPA_PLATFORM_PLUGIN_PATH 以适配当前环境
os.environ['QT_QPA_PLATFORM_PLUGIN_PATH'] = str(
    conda_env_path / "plugins" / "platforms")
os.environ['QT_QPA_PLATFORM_PLUGIN_PATH'] = '/home/chang/miniconda3/envs/ultralytics-env/plugins/platforms'


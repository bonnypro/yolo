# AI蒙皮铝屑观察助手 - 架构说明

## 项目结构

```
yolo/
├── main.py                 # 程序入口
├── config.py               # 配置和样式管理
├── core/                   # 核心业务逻辑
│   ├── __init__.py
│   ├── model_handler.py    # YOLO模型管理
│   └── video_handler.py    # 视频和录制管理
├── ui/                     # 用户界面
│   ├── __init__.py
│   └── main_window.py      # 主窗口
├── requirements.txt        # 依赖管理
└── test_architecture.py   # 架构测试脚本
```

## 架构设计原则

### 1. 单一职责原则
- **config.py**: 集中管理所有配置、样式和常量
- **model_handler.py**: 专门处理YOLO模型的加载、推理和配置
- **video_handler.py**: 专门处理视频源管理、录制和FPS计算
- **main_window.py**: 专门处理UI布局和用户交互

### 2. 松耦合设计
- 各模块通过明确的接口进行通信
- UI层不直接操作业务逻辑，而是通过handler类
- 配置与代码分离，便于维护

### 3. 高内聚
- 相关功能集中在同一模块内
- 每个模块职责明确，功能完整

## 模块详细说明

### config.py - 配置中心
```python
# 应用信息
APP_VERSION = "v1.0.0 by Chang"
APP_TITLE = "AI蒙皮铝屑观察助手"

# 默认设置
DEFAULT_SETTINGS = {
    "confidence": 0.5,
    "window_size": (1200, 800),
    # ...
}

# UI样式定义
STYLES = {
    "BACKGROUND": "background-color: #272822; color: #FFFFFF;",
    # ...
}
```

**优势**:
- 所有配置集中管理，便于修改
- 样式与逻辑分离，便于主题切换
- 减少硬编码，提高可维护性

### core/model_handler.py - 模型管理
```python
class ModelHandler:
    def load_model(self, model_path):
        # 模型加载逻辑
    
    def predict(self, frame):
        # 推理逻辑
    
    def set_confidence(self, confidence):
        # 置信度设置
```

**职责**:
- YOLO模型的加载和卸载
- 模型推理和结果处理
- 置信度阈值管理
- 模型状态信息提供

### core/video_handler.py - 视频管理
```python
class VideoHandler:
    def open_camera(self, camera_index=0):
        # 摄像头管理
    
    def open_video(self, video_path):
        # 视频文件管理
    
    def start_recording(self, record_path):
        # 录制管理
    
    def get_frame(self):
        # 帧获取
```

**职责**:
- 视频源管理（摄像头/文件）
- 视频录制功能
- FPS计算
- 跨平台视频编码器选择

### ui/main_window.py - 主窗口
```python
class MainWindow(QMainWindow):
    def __init__(self):
        self.model_handler = ModelHandler()
        self.video_handler = VideoHandler()
        # UI初始化和事件绑定
```

**职责**:
- UI布局和组件管理
- 用户事件处理
- 协调各handler的工作
- 状态显示和更新

## 通信方式

### 直接调用
```python
# 主窗口直接调用handler方法
def load_model(self):
    success = self.model_handler.load_model(path)
    if success:
        self.update_ui()
```

### 状态查询
```python
# 通过状态查询方法获取信息
if self.model_handler.is_model_loaded():
    # 执行相关操作
```

## 重构优势

### 1. 代码组织更清晰
- 原文件606行代码分散到多个职责明确的模块
- 每个文件功能单一，便于理解和维护

### 2. 便于功能扩展
- 新增功能只需在对应模块添加方法
- 不影响其他模块的稳定性

### 3. 便于测试
- 可以独立测试每个模块
- 业务逻辑与UI分离，便于单元测试

### 4. 便于维护
- 修改某个功能只需关注对应模块
- 配置集中管理，便于调整

## 使用方式

### 运行程序
```bash
python main.py
```

### 测试架构
```bash
python test_architecture.py
```

### 安装依赖
```bash
pip install -r requirements.txt
```

## 迁移说明

原文件已保留，新架构文件已创建：
- `main_window.py` (原文件) → `ui/main_window.py` (重构后)
- `video_processor.py` (原文件) → `core/video_handler.py` (重构后)
- 新增 `core/model_handler.py` (模型管理)
- 新增 `config.py` (配置管理)
- 新增 `main.py` (程序入口)

## 后续优化建议

1. **错误处理**: 在各模块中添加更完善的异常处理
2. **日志系统**: 添加日志记录功能
3. **配置文件**: 支持外部配置文件
4. **插件系统**: 为未来功能扩展预留接口 




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


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
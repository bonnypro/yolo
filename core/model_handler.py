import os
from datetime import datetime
from ultralytics import YOLO


class ModelHandler:
    def __init__(self):
        self.model = None
        self.confidence_threshold = 0.5
        self.current_model_path = None

    def load_model(self, model_path):
        """加载YOLO模型"""
        try:
            self.model = YOLO(model_path)
            self.current_model_path = model_path
            return True, f"模型加载成功: {model_path}"
        except Exception as e:
            return False, f"模型加载失败: {str(e)}"

    def load_default_model(self):
        """加载默认模型"""
        if os.path.exists("best.pt"):
            return self.load_model("best.pt")
        return False, "默认模型文件不存在"

    def predict(self, frame):
        """对帧进行推理"""
        if self.model is None:
            return frame
        
        results = self.model(frame, conf=self.confidence_threshold)
        return results[0].plot()

    def set_confidence(self, confidence):
        """设置置信度阈值"""
        self.confidence_threshold = confidence

    def get_model_info(self):
        """获取模型信息"""
        if self.current_model_path is None:
            return "未加载"
        
        model_name = os.path.basename(self.current_model_path)
        try:
            mod_time = os.path.getmtime(self.current_model_path)
            mod_time_str = datetime.fromtimestamp(mod_time).strftime('%Y-%m-%d %H:%M')
            return f"{model_name} (修改时间: {mod_time_str})"
        except Exception:
            return model_name

    def is_model_loaded(self):
        """检查模型是否已加载"""
        return self.model is not None 
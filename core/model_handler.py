import os
from datetime import datetime
from ultralytics import YOLO
import cv2
import numpy as np

from config import DETECTABLE_CLASSES


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

    def process_frame(self, frame, confidence_threshold=None, roi=None):
        """处理帧，支持ROI和置信度设置"""
        if self.model is None:
            return frame, False
        
        # 设置置信度
        if confidence_threshold is not None:
            self.confidence_threshold = confidence_threshold
        
        # 如果有ROI处理器，使用ROI检测
        if roi and hasattr(roi, 'is_roi_enabled') and roi.is_roi_enabled():
            # 创建ROI掩码
            mask = roi.create_roi_mask(frame.shape)
            
            # 在ROI区域内进行检测
            results = self.model(frame, conf=self.confidence_threshold, classes=DETECTABLE_CLASSES)
            
            # 先获取所有检测框
            boxes = results[0].boxes.xyxy.cpu().numpy()
            confs = results[0].boxes.conf.cpu().numpy()
            class_ids = results[0].boxes.cls.cpu().numpy().astype(int)

            # 过滤出在ROI区域内的检测框
            filtered_boxes = []
            detected_class0 = False
            if len(boxes) > 0:
                roi_points = np.array(roi.get_roi_points(roi.get_active_roi_name()), dtype=np.int32)
                for i, box in enumerate(boxes):
                    x1, y1, x2, y2 = box
                    center_x, center_y = (x1 + x2) / 2, (y1 + y2) / 2
                    if cv2.pointPolygonTest(roi_points, (center_x, center_y), False) >= 0:
                        filtered_boxes.append((box, confs[i], class_ids[i]))
                        if class_ids[i] == 0:
                            detected_class0 = True
            
            # 在原始帧的副本上绘制过滤后的检测框
            result_frame = frame.copy()
            for box, conf, class_id in filtered_boxes:
                x1, y1, x2, y2 = map(int, box)
                label = f"{self.model.names[class_id]} {conf:.2f}"
                cv2.rectangle(result_frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                cv2.putText(result_frame, label, (x1, y1 - 10), 
                            cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 0), 2)
            
            return result_frame, detected_class0
        else:
            # 正常检测
            results = self.model(frame, conf=self.confidence_threshold, classes=DETECTABLE_CLASSES)
            return results[0].plot(), False

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
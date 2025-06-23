import cv2
import numpy as np
import json
import os
import re
import logging
import traceback
import glob
from datetime import datetime
from typing import List, Tuple, Optional, Dict, Any
from config import ROI_CONFIG

# 设置日志记录器
logger = logging.getLogger(__name__)

class ROIHandler:
    def __init__(self):
        self.roi_configs = {}  # 存储多个ROI配置
        self.active_roi = None  # 当前激活的ROI名称
        self.roi_enabled = False  # ROI是否启用
        self.roi_mode = False  # 是否处于ROI绘制模式
        self.current_points = []  # 当前正在绘制的点
        self.roi_folder = ROI_CONFIG["roi_folder"]  # ROI文件夹
        self.temp_file = os.path.join(self.roi_folder, ROI_CONFIG["temp_roi_file"])  # 临时ROI文件
        self._saving = False  # 防止保存过程中重新加载
        self.max_roi_count = ROI_CONFIG["max_roi_count"]  # 最大ROI数量限制
        self.max_points = ROI_CONFIG["max_points"]  # 最大点数
        
        # 确保ROI文件夹存在
        self._ensure_roi_folder()
        
        # 加载配置
        self.load_config()

    def _ensure_roi_folder(self):
        """确保ROI文件夹存在"""
        if not os.path.exists(self.roi_folder):
            os.makedirs(self.roi_folder)
            logger.info(f"创建ROI文件夹: {self.roi_folder}")

    def _clear_temp_roi(self):
        """清除临时ROI文件"""
        if os.path.exists(self.temp_file):
            try:
                os.remove(self.temp_file)
                logger.info("清除临时ROI文件")
            except Exception as e:
                logger.error(f"清除临时ROI文件失败: {e}")

    def _get_roi_file_path(self, roi_name: str) -> str:
        """获取ROI文件路径"""
        return os.path.join(self.roi_folder, f"{roi_name}.json")

    def _load_roi_from_file(self, roi_name: str) -> Optional[Dict[str, Any]]:
        """从文件加载单个ROI配置"""
        roi_file = self._get_roi_file_path(roi_name)
        if not os.path.exists(roi_file):
            return None
        
        try:
            with open(roi_file, 'r', encoding='utf-8') as f:
                roi_config = json.load(f)
            return roi_config
        except Exception as e:
            logger.error(f"加载ROI文件失败 {roi_file}: {e}")
            return None

    def _save_roi_to_file(self, roi_name: str, roi_config: Dict[str, Any]) -> bool:
        """保存ROI配置到文件"""
        roi_file = self._get_roi_file_path(roi_name)
        try:
            # 使用临时文件来避免写入过程中的问题
            temp_file = roi_file + ".tmp"
            with open(temp_file, 'w', encoding='utf-8') as f:
                json.dump(roi_config, f, ensure_ascii=False, indent=2)
                f.flush()
                os.fsync(f.fileno())
            
            # 如果临时文件写入成功，则替换原文件
            if os.path.exists(temp_file):
                if os.path.exists(roi_file):
                    os.remove(roi_file)
                os.rename(temp_file, roi_file)
                logger.info(f"ROI配置已保存到文件: {roi_file}")
                return True
            else:
                logger.error("临时文件创建失败")
                return False
                
        except Exception as e:
            logger.error(f"保存ROI文件失败 {roi_file}: {e}")
            # 如果临时文件存在，尝试删除
            if os.path.exists(temp_file):
                try:
                    os.remove(temp_file)
                except:
                    pass
            return False

    def _delete_roi_file(self, roi_name: str) -> bool:
        """删除ROI文件"""
        roi_file = self._get_roi_file_path(roi_name)
        if os.path.exists(roi_file):
            try:
                os.remove(roi_file)
                logger.info(f"删除ROI文件: {roi_file}")
                return True
            except Exception as e:
                logger.error(f"删除ROI文件失败 {roi_file}: {e}")
                return False
        return False

    def _scan_roi_files(self) -> List[str]:
        """扫描ROI文件夹，获取所有ROI名称"""
        roi_names = []
        if not os.path.exists(self.roi_folder):
            return roi_names
        
        try:
            # 获取所有.json文件，排除临时和主配置文件
            roi_files = glob.glob(os.path.join(self.roi_folder, "*.json"))
            for roi_file in roi_files:
                filename = os.path.basename(roi_file)
                if filename not in [ROI_CONFIG["temp_roi_file"], ROI_CONFIG["main_config_file"]]:
                    roi_name = os.path.splitext(filename)[0]
                    roi_names.append(roi_name)
            
            logger.info(f"扫描到ROI文件: {roi_names}")
            return roi_names
        except Exception as e:
            logger.error(f"扫描ROI文件失败: {e}")
            return []

    def start_drawing(self):
        """开始绘制新的ROI"""
        self.roi_mode = True
        self.current_points = []
        # 清除之前的临时文件
        self._clear_temp_roi()

    def stop_drawing(self):
        """停止绘制"""
        self.roi_mode = False
        self.current_points = []
        # 清除临时文件
        self._clear_temp_roi()

    def add_point(self, x: int, y: int) -> bool:
        """添加ROI顶点"""
        if not self.roi_mode:
            return False
        
        if len(self.current_points) >= self.max_points:
            return False

        self.current_points.append([x, y])
        
        # 保存临时ROI文件
        self._save_temp_roi()
        
        return True

    def _save_temp_roi(self):
        """保存临时ROI文件"""
        if len(self.current_points) >= 3:
            temp_config = {
                "name": "temp_roi",
                "points": self.current_points.copy(),
                "created_time": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                "last_used": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            
            try:
                with open(self.temp_file, 'w', encoding='utf-8') as f:
                    json.dump(temp_config, f, ensure_ascii=False, indent=2)
                    f.flush()
                    os.fsync(f.fileno())
                logger.info("临时ROI文件已保存")
            except Exception as e:
                logger.error(f"保存临时ROI文件失败: {e}")

    def clear_current_roi(self) -> bool:
        """清除当前选中的ROI"""
        if self.active_roi:
            # 从内存中删除
            if self.active_roi in self.roi_configs:
                del self.roi_configs[self.active_roi]
            
            # 删除文件
            if self._delete_roi_file(self.active_roi):
                self.active_roi = None
                self.save_config()
                return True
        return False

    def clear_drawing_points(self):
        """清除正在绘制的点"""
        self.current_points = []
        # 清除临时文件
        self._clear_temp_roi()

    def can_create_roi(self) -> bool:
        """检查是否可以创建新的ROI"""
        return len(self.roi_configs) < self.max_roi_count

    def is_roi_name_exists(self, roi_name: str) -> bool:
        """检查ROI名称是否已在内存中"""
        return roi_name in self.roi_configs

    def is_roi_file_exists(self, roi_name: str) -> bool:
        """检查ROI文件是否已存在于硬盘上"""
        roi_file = self._get_roi_file_path(roi_name)
        return os.path.exists(roi_file)

    def generate_unique_roi_name(self) -> str:
        """扫描文件夹并生成一个唯一的ROI名称"""
        existing_names = self._scan_roi_files()
        base_name = "ROI"
        counter = 1
        while True:
            new_name = f"{base_name}_{counter}"
            if new_name not in existing_names:
                return new_name
            counter += 1

    def finish_roi_drawing(self, roi_name: str) -> bool:
        """完成ROI绘制"""
        logger.info(f"开始完成ROI绘制: {roi_name}, 当前点数: {len(self.current_points)}")
        
        # 检查ROI数量限制
        if len(self.roi_configs) >= self.max_roi_count:
            logger.warning(f"ROI数量已达上限({self.max_roi_count})，无法创建新ROI")
            return False
        
        if len(self.current_points) < 3:
            logger.warning(f"ROI点数不足，无法保存: {len(self.current_points)}")
            return False
        
        # 检查名称是否已存在
        if self.is_roi_name_exists(roi_name):
            logger.warning(f"ROI名称 '{roi_name}' 已存在，请使用不同的名称")
            return False
        
        # 创建ROI配置
        roi_config = {
            "name": roi_name,
            "points": self.current_points.copy(),
            "created_time": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            "last_used": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        
        logger.info(f"保存前ROI数量: {len(self.roi_configs)}")
        logger.info(f"保存前ROI名称: {list(self.roi_configs.keys())}")
        
        # 保存到文件
        if self._save_roi_to_file(roi_name, roi_config):
            # 添加到内存配置中
            self.roi_configs[roi_name] = roi_config
            
            logger.info(f"保存后ROI数量: {len(self.roi_configs)}")
            logger.info(f"保存后ROI名称: {list(self.roi_configs.keys())}")
            
            # 设置新创建的ROI为活动ROI
            self.active_roi = roi_name
            logger.info(f"设置活动ROI为: {roi_name}")
            
            # 保存配置到文件
            self.save_config()
            
            # 停止绘制模式
            self.stop_drawing()
            
            logger.info(f"ROI绘制完成: {roi_name}, 最终ROI数量: {len(self.roi_configs)}")
            return True
        else:
            logger.error(f"保存ROI文件失败: {roi_name}")
            return False

    def update_roi_points(self, roi_name: str, points: List[List[int]]) -> bool:
        """更新ROI点坐标"""
        if roi_name in self.roi_configs:
            if len(points) > self.max_points:
                return False
            self.roi_configs[roi_name]["points"] = points
            self.roi_configs[roi_name]["last_used"] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            if self._save_roi_to_file(roi_name, self.roi_configs[roi_name]):
                self.save_config()
                return True
        return False

    def get_roi_points(self, roi_name: str = None) -> List[List[int]]:
        """获取ROI点坐标"""
        if roi_name is None:
            roi_name = self.active_roi
        
        if roi_name and roi_name in self.roi_configs:
            return self.roi_configs[roi_name]["points"]
        return []

    def get_current_points(self) -> List[List[int]]:
        """获取当前正在绘制的点"""
        return self.current_points.copy()

    def has_roi(self) -> bool:
        """检查是否有ROI配置"""
        return len(self.roi_configs) > 0

    def has_active_roi(self) -> bool:
        """检查是否有激活的ROI"""
        return self.active_roi is not None and self.active_roi in self.roi_configs

    def is_roi_enabled(self) -> bool:
        """检查ROI是否启用"""
        return self.roi_enabled and self.has_active_roi()

    def set_roi_enabled(self, enabled: bool):
        """设置ROI启用状态"""
        self.roi_enabled = enabled
        self.save_config()

    def set_active_roi(self, roi_name: str):
        """设置激活的ROI"""
        logger.info(f"设置活动ROI: {roi_name}, 当前ROI数量: {len(self.roi_configs)}")
        
        if roi_name is None:
            # 清除活动ROI
            self.active_roi = None
            self.save_config()
        elif roi_name in self.roi_configs:
            # 设置已存在的ROI为活动ROI
            self.active_roi = roi_name
            self.roi_configs[roi_name]["last_used"] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            self.save_config()
        else:
            logger.warning(f"尝试设置不存在的ROI为活动ROI: {roi_name}")
        
        logger.info(f"设置活动ROI后，当前ROI数量: {len(self.roi_configs)}")

    def get_roi_names(self) -> List[str]:
        """获取所有ROI名称"""
        return list(self.roi_configs.keys())

    def get_active_roi_name(self) -> str:
        """获取当前激活的ROI名称"""
        return self.active_roi or ""

    def get_roi_count(self) -> int:
        """获取当前ROI数量"""
        return len(self.roi_configs)

    def get_max_roi_count(self) -> int:
        """获取最大ROI数量"""
        return self.max_roi_count

    def create_roi_mask(self, frame_shape: Tuple[int, int, int]) -> np.ndarray:
        """创建ROI掩码"""
        if not self.is_roi_enabled():
            return np.ones(frame_shape[:2], dtype=np.uint8) * 255
        
        mask = np.zeros(frame_shape[:2], dtype=np.uint8)
        points = self.get_roi_points()
        
        if len(points) >= 3:
            points_array = np.array(points, dtype=np.int32)
            cv2.fillPoly(mask, [points_array], 255)
        
        return mask

    def is_point_in_roi(self, x: int, y: int) -> bool:
        """判断点是否在ROI内"""
        if not self.is_roi_enabled():
            return True
        
        points = self.get_roi_points()
        if len(points) < 3:
            return True
        
        points_array = np.array(points, dtype=np.int32)
        return cv2.pointPolygonTest(points_array, (x, y), False) >= 0

    def apply_roi_to_frame(self, frame: np.ndarray) -> np.ndarray:
        """将ROI应用到帧上"""
        if not self.is_roi_enabled():
            return frame
        
        mask = self.create_roi_mask(frame.shape)
        return cv2.bitwise_and(frame, frame, mask=mask)

    def draw_roi_on_frame(self, frame: np.ndarray, draw_current: bool = True) -> np.ndarray:
        """在帧上绘制ROI"""
        result_frame = frame.copy()
        
        # 绘制当前正在绘制的点
        if draw_current and self.roi_mode and len(self.current_points) > 0:
            for i, point in enumerate(self.current_points):
                cv2.circle(result_frame, tuple(point), 5, (255, 0, 0), -1)
                cv2.putText(result_frame, str(i+1), (point[0]+10, point[1]-10), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
            
            # 绘制连接线
            if len(self.current_points) > 1:
                for i in range(len(self.current_points) - 1):
                    cv2.line(result_frame, tuple(self.current_points[i]), 
                            tuple(self.current_points[i+1]), (0, 255, 0), 2)
        
        # 绘制激活的ROI
        if self.has_active_roi():
            points = self.get_roi_points()
            if len(points) >= 3:
                points_array = np.array(points, dtype=np.int32)
                cv2.polylines(result_frame, [points_array], True, (0, 255, 0), 2)
                
                # 绘制顶点
                for i, point in enumerate(points):
                    cv2.circle(result_frame, tuple(point), 5, (255, 0, 0), -1)
                    cv2.putText(result_frame, str(i+1), (point[0]+10, point[1]-10), 
                               cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
        
        return result_frame

    @staticmethod
    def validate_coordinate(text: str) -> Optional[Tuple[int, int]]:
        """验证坐标输入格式"""
        # 支持格式: "100,150", "100, 150", "100 150"
        pattern = r'^\s*(\d+)\s*[,，]\s*(\d+)\s*$|^\s*(\d+)\s+(\d+)\s*$'
        match = re.match(pattern, text)
        if match:
            groups = match.groups()
            if groups[0] and groups[1]:
                return int(groups[0]), int(groups[1])
            elif groups[2] and groups[3]:
                return int(groups[2]), int(groups[3])
        return None

    def save_config(self):
        """保存配置到文件"""
        if self._saving:
            logger.warning("正在保存配置，跳过重复保存")
            return
            
        self._saving = True
        
        # 添加详细的调试信息
        logger.info(f"开始保存配置，当前ROI配置: {list(self.roi_configs.keys())}")
        
        config = {
            "roi_settings": {
                "roi_enabled": self.roi_enabled,
                "active_roi": self.active_roi
            }
        }
        
        try:
            # 使用临时文件来避免写入过程中的问题
            config_file = os.path.join(self.roi_folder, "roi_config.json")
            temp_file = config_file + ".tmp"
            with open(temp_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, ensure_ascii=False, indent=2)
                f.flush()  # 确保数据写入磁盘
                os.fsync(f.fileno())  # 强制同步到磁盘
            
            # 如果临时文件写入成功，则替换原文件
            if os.path.exists(temp_file):
                if os.path.exists(config_file):
                    os.remove(config_file)
                os.rename(temp_file, config_file)
                logger.info(f"ROI配置已保存，当前ROI数量: {len(self.roi_configs)}")
                
                # 验证保存后的文件内容
                try:
                    with open(config_file, 'r', encoding='utf-8') as f:
                        saved_config = json.load(f)
                    logger.info(f"配置保存成功")
                except Exception as e:
                    logger.error(f"验证保存文件失败: {e}")
            else:
                logger.error("临时文件创建失败")
                
        except Exception as e:
            logger.error(f"保存ROI配置失败: {e}")
            # 如果临时文件存在，尝试删除
            if os.path.exists(temp_file):
                try:
                    os.remove(temp_file)
                except:
                    pass
        finally:
            self._saving = False

    def load_config(self):
        """从文件加载配置"""
        # 添加调用栈信息
        stack_trace = traceback.format_stack()
        logger.info(f"load_config被调用，调用栈: {stack_trace[-3:]}")  # 只显示最后3层
        
        if self._saving:
            logger.warning("正在保存配置，跳过加载")
            return
        
        # 清除临时文件
        self._clear_temp_roi()
        
        # 加载主配置文件
        config_file = os.path.join(self.roi_folder, "roi_config.json")
        if os.path.exists(config_file):
            try:
                with open(config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                
                roi_settings = config.get("roi_settings", {})
                old_roi_count = len(self.roi_configs)
                old_roi_names = list(self.roi_configs.keys())
                
                logger.info(f"加载配置前ROI数量: {old_roi_count}, ROI名称: {old_roi_names}")
                
                self.roi_enabled = roi_settings.get("roi_enabled", False)
                self.active_roi = roi_settings.get("active_roi")
                
            except Exception as e:
                logger.error(f"加载主配置文件失败: {e}")
        
        # 扫描并加载所有ROI文件
        roi_names = self._scan_roi_files()
        self.roi_configs = {}
        
        for roi_name in roi_names:
            roi_config = self._load_roi_from_file(roi_name)
            if roi_config:
                self.roi_configs[roi_name] = roi_config
        
        new_roi_count = len(self.roi_configs)
        new_roi_names = list(self.roi_configs.keys())
        logger.info(f"ROI配置已加载，ROI数量变化: {old_roi_count} -> {new_roi_count}")
        logger.info(f"ROI名称变化: {old_roi_names} -> {new_roi_names}")
        
        # 验证活动ROI是否仍然存在
        if self.active_roi and self.active_roi not in self.roi_configs:
            logger.warning(f"活动ROI '{self.active_roi}' 不存在，清除活动ROI")
            self.active_roi = None

    def get_config_data(self) -> Dict[str, Any]:
        """获取配置数据"""
        return {
            "roi_enabled": self.roi_enabled,
            "active_roi": self.active_roi,
            "roi_configs": self.roi_configs.copy()
        }

    def rename_roi(self, old_name: str, new_name: str) -> bool:
        """重命名ROI"""
        if old_name in self.roi_configs and new_name not in self.roi_configs:
            # 复制配置，删除旧的
            self.roi_configs[new_name] = self.roi_configs.pop(old_name)
            self.roi_configs[new_name]['name'] = new_name
            
            # 如果重命名的是当前激活的ROI，则更新激活名称
            if self.active_roi == old_name:
                self.active_roi = new_name
            
            # 保存新文件
            if self._save_roi_to_file(new_name, self.roi_configs[new_name]):
                # 删除旧文件
                self._delete_roi_file(old_name)
                self.save_config()
                return True
        return False 
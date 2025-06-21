#!/usr/bin/env python3
"""
测试新架构的各个模块
"""

def test_imports():
    """测试模块导入"""
    try:
        from config import APP_VERSION, STYLES, DEFAULT_SETTINGS
        print("✓ config.py 导入成功")
        
        from core.model_handler import ModelHandler
        print("✓ ModelHandler 导入成功")
        
        from core.video_handler import VideoHandler
        print("✓ VideoHandler 导入成功")
        
        from ui.main_window import MainWindow
        print("✓ MainWindow 导入成功")
        
        return True
    except Exception as e:
        print(f"✗ 导入失败: {e}")
        return False

def test_model_handler():
    """测试模型处理器"""
    try:
        from core.model_handler import ModelHandler
        
        handler = ModelHandler()
        print("✓ ModelHandler 创建成功")
        
        # 测试默认模型加载
        success, message = handler.load_default_model()
        print(f"✓ 默认模型加载: {message}")
        
        # 测试置信度设置
        handler.set_confidence(0.7)
        assert handler.confidence_threshold == 0.7
        print("✓ 置信度设置成功")
        
        return True
    except Exception as e:
        print(f"✗ ModelHandler 测试失败: {e}")
        return False

def test_video_handler():
    """测试视频处理器"""
    try:
        from core.video_handler import VideoHandler
        
        handler = VideoHandler()
        print("✓ VideoHandler 创建成功")
        
        # 测试视频源状态
        assert not handler.is_video_ready()
        print("✓ 视频源状态检查成功")
        
        # 测试录制状态
        assert not handler.is_recording()
        print("✓ 录制状态检查成功")
        
        return True
    except Exception as e:
        print(f"✗ VideoHandler 测试失败: {e}")
        return False

def test_config():
    """测试配置"""
    try:
        from config import APP_VERSION, STYLES, DEFAULT_SETTINGS
        
        assert APP_VERSION == "v1.0.0 by Chang"
        print("✓ 应用版本配置正确")
        
        assert "BACKGROUND" in STYLES
        print("✓ 样式配置正确")
        
        assert "confidence" in DEFAULT_SETTINGS
        print("✓ 默认设置配置正确")
        
        return True
    except Exception as e:
        print(f"✗ 配置测试失败: {e}")
        return False

def main():
    """主测试函数"""
    print("开始测试新架构...")
    print("=" * 50)
    
    tests = [
        ("模块导入测试", test_imports),
        ("配置测试", test_config),
        ("模型处理器测试", test_model_handler),
        ("视频处理器测试", test_video_handler),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n{test_name}:")
        if test_func():
            passed += 1
        else:
            print(f"  {test_name} 失败")
    
    print("\n" + "=" * 50)
    print(f"测试结果: {passed}/{total} 通过")
    
    if passed == total:
        print("🎉 所有测试通过！新架构工作正常。")
        return True
    else:
        print("❌ 部分测试失败，请检查错误信息。")
        return False

if __name__ == "__main__":
    main() 
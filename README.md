# yolo


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


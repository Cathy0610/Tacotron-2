# Environment Setup

## 使用已配置好的虚拟环境

实验室服务器已配置好 miniconda 以及部分公用的环境，可直接使用。方法如下：

- 在个人环境配置文件 ```~/.bashrc``` 中增加 miniconda 的路径：
```bash
export PATH="/ceph/runtime/miniconda3/bin:$PATH"
```

- 激活所需环境：（以 rayhane-taco2 为例） 
```bash
source activate rayhane-taco2
```

## 从environment.yaml中创建环境

## 从头开始配置全新环境

### 安装 Anaconda or Miniconda

- 可以从清华镜像站查看使用帮助：https://mirrors.tuna.tsinghua.edu.cn/help/anaconda/

- 实验室服务器已配置好miniconda，可在个人环境配置文件 ```~/.bashrc``` 中增加miniconda的路径后直接使用（跳到第2步）：
```bash
export PATH="/ceph/runtime/miniconda3/bin:$PATH"
```

- 以下以anaconda为例，说明安装过程：

  - 下载
    (对应python版本和操作系统版本: https://mirrors.tuna.tsinghua.edu.cn/anaconda/archive/)
    ```bash
    wget https://mirrors.tuna.tsinghua.edu.cn/anaconda/archive/Anaconda3-4.2.0-Linux-x86_64.sh
    ```
  - 安装
    ```bash
    bash Anaconda3-4.2.0-Linux-x86_64.sh
    ```
  - 升级
    (参考: https://stackoverflow.com/questions/38972052/anaconda-update-all-possible-packages)
    ```bash
    conda upgrade --all
    ```
  - 添加channels
    (参考: https://blog.csdn.net/weixin_43949246/article/details/109637468)   
    因为conda 下载文件要用到国外的服务器，速度一般会比较慢，我们可以通过增加国内镜像服务器来解决。
    ```bash
    #中国科技大学的源
    conda config --add channels http://mirrors.ustc.edu.cn/anaconda/pkgs/main/
    conda config --add channels http://mirrors.ustc.edu.cn/anaconda/pkgs/free/
    conda config --add channels http://mirrors.ustc.edu.cn/anaconda/cloud/conda-forge/
    ```

### 配置新的环境

#### 1. Create conda environment

使用以下命令创建虚拟环境，创建时给定虚拟环境名字和python、pip版本：
```bash
conda create -n tfenv pip=20 python=3.5
```

注：如要删除虚拟环境，命令为：
```bash
conda remove -n tfenv --all
```

#### 2. Activate the environment

使用以下命令激活虚拟环境：
```bash
source activate tfenv
```

注：使用后，可通过如下命令退出虚拟环境：
```bash
conda deactivate
```

#### 3. Install CUDA framework

```bash
conda install cudatoolkit=10.0 cudnn=7.6 cupti=10.0 blas numpy pip=20 scipy cython
```

NVIDIA gpu—硬件，驱动，cuda--并行计算框架，cudnn-加速库

#### 4. Install Tensorflow 1.13.1

安装Tensorflow gpu版本，gpu版本要和cuda版本对应：
```bash
pip install --ignore-installed --upgrade   https://storage.googleapis.com/tensorflow/linux/gpu/tensorflow_gpu-1.13.1-cp35-cp35m-linux_x86_64.whl
```

或者使用国内镜像：
```bash
pip install -i https://pypi.tuna.tsinghua.edu.cn/simple --ignore-installed --upgrade http://mirrors.aliyun.com/pypi/packages/ce/e4/be6d7d17d727b0d2e10d30a87de4e56b8661075eccb8032a8aa5cc84c300/tensorflow_gpu-1.13.1-cp35-cp35m-manylinux1_x86_64.whl#sha256=408eb4ea8adde5dc8c99a72dc678814844a160d8d37c43e677e67ba484d80ab3
```

Tensorflow安装包地址：https://www.tensorflow.org/install/pip#package-location

#### 5. Install Tacotron2 requirements

安装Tacotron2所需的库文件：
```bash
pip install -r requirements.txt
```

注意：和3.5版本Python适配的llvmlite版本为0.31.0。因此需要修改requirements.txt，增加：llvmlite==0.31.0

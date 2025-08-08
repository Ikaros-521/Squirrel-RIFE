# SVFI 安装指南

## 系统要求

- Windows 10 及以上操作系统
- NVIDIA 显卡需要 GeForce Experience 所安装的驱动版本大于等于460.89
- 2GB 以上显存, 4GB 左右的空余运行内存以及4GB+的磁盘剩余空间

## 安装步骤

### 1. 安装Python环境

首先，确保您已安装Python 3.7或更高版本。您可以从[Python官网](https://www.python.org/downloads/)下载并安装。

### 2. 安装依赖包

在项目根目录下运行以下命令安装所需依赖：

```bash
pip install -r requirements.txt
```

### 3. 安装FFmpeg

SVFI需要FFmpeg进行视频处理。您可以从[FFmpeg官网](https://ffmpeg.org/download.html)下载并安装，或使用以下方法：

#### Windows用户

1. 下载FFmpeg：https://ffmpeg.org/download.html
2. 解压到任意目录
3. 将FFmpeg的bin目录添加到系统环境变量PATH中

## 命令行使用

SVFI提供了命令行工具，可以通过以下方式使用：

```bash
python one_line_shot_args.py -i <输入路径> -c <配置文件路径> -t <任务ID> [可选参数]
```

### 必需参数

- `-i, --input`：原视频/图片序列文件夹路径
- `-c, --config`：配置文件路径
- `-t, --task-id`：任务ID

### 可选参数

- `--concat-only`：只执行合并已有区块操作
- `--extract-only`：只执行拆帧操作
- `--render-only`：只执行渲染操作

### 配置文件示例

```ini
[General]
output_dir=输出目录路径
output_ext=.mp4
is_save_audio=true
use_scdet_fixed=false
is_no_scdet=false
is_scdet_mix=false
scdet_threshold=12
use_sr=false
use_rife_multi_cards=false
use_rife_auto_scale=false
use_rife_fp16=false
use_rife_trt=false
use_rife_tta=false
use_rife_ensemble=false
use_rife_backward_flow=false
use_rife_multi_cards=false
use_rife_uhd=false
use_rife_interp=false
use_rife_sc_dropout=false
use_rife_algo=official_2.3
rife_scale=0.5
rife_device_id=0
target_fps=60
render_encoder=CPU
render_encoder_preset=fast
render_encoder_tune=film
render_encoder_profile=high
render_encoder_level=4.1
render_encoder_crf=16
render_encoder_codec=H264,8bit
render_encoder_thread=0
render_encoder_custom_params=
render_chunk_size=100
render_buffer_size=0
render_hdr_mode=Auto
render_hdr_custom_params=
render_fast_decode=false
render_hwaccel=false
render_deinterlace=false
render_denoise=false
render_default_encoder=true
render_audio_to_aac=false
render_keep_chunk=false
render_high_precision=false
```

### 使用示例

```bash
python one_line_shot_args.py -i "input.mp4" -c "svfi_config.ini" -t "test_task"
```

## 常见问题

### 显存不足

如果遇到显存不足的问题，可以尝试以下方法：

1. 在配置文件中设置 `use_rife_fp16=true` 启用半精度模式
2. 减小 `rife_scale` 值（例如设置为0.5）
3. 减小输入视频分辨率

### 补帧效果不佳

如果补帧效果不理想，可以尝试：

1. 调整 `scdet_threshold` 值（转场检测阈值）
2. 尝试不同的 `rife_algo` 模型
3. 启用 `use_rife_tta` 或 `use_rife_ensemble` 提高质量（但会降低速度）
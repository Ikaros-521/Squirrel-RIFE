# coding: utf-8
import os
import sys
import tempfile
import shutil
import configparser
import gradio as gr
import numpy as np
import cv2
import torch
from pathlib import Path

# 添加SVFI目录到系统路径
svfi_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "SVFI 3.x")
sys.path.append(svfi_path)

# 导入SVFI相关模块
try:
    from Utils.utils import DefaultConfigParser, Tools
    from Utils.StaticParameters import HDR_STATE
except ImportError:
    print("无法导入SVFI模块，请确保SVFI 3.x目录存在且包含必要文件")
    sys.exit(1)

# 检查CUDA是否可用
use_cuda = torch.cuda.is_available()
if not use_cuda:
    print("警告: CUDA不可用，将使用CPU模式，这会极大降低处理速度")

# 创建临时目录用于存储处理文件
temp_dir = tempfile.mkdtemp()
print(f"临时目录: {temp_dir}")

# 创建默认配置文件
def create_default_config(output_dir):
    config = configparser.ConfigParser()
    config["General"] = {
        "output_dir": output_dir,
        "output_ext": ".mp4",
        "is_save_audio": "true",
        "use_scdet_fixed": "false",
        "is_no_scdet": "false",
        "is_scdet_mix": "false",
        "scdet_threshold": "12",
        "use_sr": "false",
        "use_rife_multi_cards": "false",
        "use_rife_auto_scale": "false",
        "use_rife_fp16": "true",  # 默认使用半精度模式以节省显存
        "use_rife_trt": "false",
        "use_rife_tta": "false",
        "use_rife_ensemble": "false",
        "use_rife_backward_flow": "false",
        "use_rife_multi_cards": "false",
        "use_rife_uhd": "false",
        "use_rife_interp": "false",
        "use_rife_sc_dropout": "false",
        "use_rife_algo": "official_3.x",
        "rife_scale": "0.5",
        "rife_device_id": "0",
        "target_fps": "60",
        "render_encoder": "CPU",
        "render_encoder_preset": "fast",
        "render_encoder_tune": "film",
        "render_encoder_profile": "high",
        "render_encoder_level": "4.1",
        "render_encoder_crf": "16",
        "render_encoder_codec": "H264,8bit",
        "render_encoder_thread": "0",
        "render_encoder_custom_params": "",
        "render_chunk_size": "100",
        "render_buffer_size": "0",
        "render_hdr_mode": "Auto",
        "render_hdr_custom_params": "",
        "render_fast_decode": "false",
        "render_hwaccel": "false",
        "render_deinterlace": "false",
        "render_denoise": "false",
        "render_default_encoder": "true",
        "render_audio_to_aac": "false",
        "render_keep_chunk": "false",
        "render_high_precision": "false"
    }
    
    config_path = os.path.join(temp_dir, "svfi_config.ini")
    with open(config_path, "w", encoding="utf-8") as f:
        config.write(f)
    
    return config_path

# 运行SVFI处理视频
def process_video(input_path, target_fps, use_fp16, rife_scale, scdet_threshold, crf_value):
    # 创建输出目录
    output_dir = os.path.join(temp_dir, "output")
    os.makedirs(output_dir, exist_ok=True)
    
    # 创建配置文件
    config_path = create_default_config(output_dir)
    
    # 更新配置文件中的参数
    config = DefaultConfigParser()
    config.read(config_path, encoding="utf-8")
    
    # 更新用户设置的参数
    config["General"]["target_fps"] = str(target_fps)
    config["General"]["use_rife_fp16"] = "true" if use_fp16 else "false"
    config["General"]["rife_scale"] = str(rife_scale)
    config["General"]["scdet_threshold"] = str(scdet_threshold)
    config["General"]["render_encoder_crf"] = str(crf_value)
    
    # 保存更新后的配置
    with open(config_path, "w", encoding="utf-8") as f:
        config.write(f)
    
    # 生成任务ID
    task_id = f"gradio_task_{os.path.basename(input_path)}"
    
    # 构建SVFI命令
    cmd = f"python \"{os.path.join(svfi_path, 'one_line_shot_args.py')}\" -i \"{input_path}\" -c \"{config_path}\" -t \"{task_id}\""
    
    # 执行命令
    print(f"执行命令: {cmd}")
    result = os.system(cmd)
    
    if result != 0:
        return None, f"处理失败，错误代码: {result}"
    
    # 查找输出文件
    output_files = list(Path(output_dir).glob("*.mp4"))
    if not output_files:
        return None, "处理完成，但未找到输出文件"
    
    output_file = str(output_files[0])
    return output_file, f"处理成功: {output_file}"

# 创建Gradio界面
def create_interface():
    with gr.Blocks(title="SVFI Gradio Demo") as demo:
        gr.Markdown("# SVFI 视频补帧 Gradio Demo")
        gr.Markdown("上传视频文件，设置参数，然后点击'开始处理'按钮进行补帧。")
        
        with gr.Row():
            with gr.Column(scale=1):
                input_video = gr.Video(label="输入视频")
                
                with gr.Group():
                    gr.Markdown("### 补帧参数设置")
                    target_fps = gr.Slider(minimum=24, maximum=120, value=60, step=1, label="目标帧率")
                    use_fp16 = gr.Checkbox(value=True, label="使用半精度模式 (节省显存)")
                    rife_scale = gr.Slider(minimum=0.1, maximum=1.0, value=0.5, step=0.1, label="光流尺度 (越小越省显存)")
                    scdet_threshold = gr.Slider(minimum=1, maximum=30, value=12, step=1, label="转场检测阈值")
                    crf_value = gr.Slider(minimum=0, maximum=51, value=16, step=1, label="CRF值 (越小质量越高)")
                
                process_btn = gr.Button("开始处理", variant="primary")
            
            with gr.Column(scale=1):
                output_video = gr.Video(label="输出视频")
                output_message = gr.Textbox(label="处理信息")
        
        # 处理函数
        def process(video, fps, fp16, scale, threshold, crf):
            if video is None:
                return None, "请先上传视频"
            
            # 保存上传的视频到临时文件
            input_path = os.path.join(temp_dir, "input.mp4")
            shutil.copy(video, input_path)
            
            # 处理视频
            output_path, message = process_video(input_path, fps, fp16, scale, threshold, crf)
            
            if output_path:
                return output_path, message
            else:
                return None, message
        
        # 绑定处理按钮
        process_btn.click(
            fn=process,
            inputs=[input_video, target_fps, use_fp16, rife_scale, scdet_threshold, crf_value],
            outputs=[output_video, output_message]
        )
        
        # 添加示例
        gr.Examples(
            examples=[
                ["example.mp4", 60, True, 0.5, 12, 16],
            ],
            inputs=[input_video, target_fps, use_fp16, rife_scale, scdet_threshold, crf_value],
        )
        
        # 添加使用说明
        gr.Markdown("""
        ## 使用说明
        
        1. 上传视频文件（支持大多数常见格式）
        2. 调整参数：
           - **目标帧率**：设置输出视频的帧率，通常为原始帧率的整数倍
           - **半精度模式**：启用可节省显存，但可能略微降低质量
           - **光流尺度**：控制光流计算的精度，较小的值可节省显存
           - **转场检测阈值**：控制转场检测的灵敏度，值越小越灵敏
           - **CRF值**：控制输出视频的质量，值越小质量越高（文件越大）
        3. 点击"开始处理"按钮
        4. 等待处理完成后下载结果视频
        
        **注意**：处理大型视频可能需要较长时间，请耐心等待。
        """)
    
    return demo

# 清理函数
def cleanup():
    try:
        shutil.rmtree(temp_dir)
        print(f"已清理临时目录: {temp_dir}")
    except Exception as e:
        print(f"清理临时目录时出错: {e}")

# 主函数
def main():
    try:
        # 创建并启动Gradio界面
        demo = create_interface()
        demo.launch(server_name="0.0.0.0", share=False, inbrowser=True)
    except KeyboardInterrupt:
        print("程序被用户中断")
    except Exception as e:
        print(f"发生错误: {e}")
    finally:
        # 清理临时文件
        cleanup()

if __name__ == "__main__":
    main()
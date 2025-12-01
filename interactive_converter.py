#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
交互式 Jupyter Notebook 到 PDF 转换工具
在 Linux 环境中使用，引导用户输入必要信息并执行转换
"""

import os
import sys
import subprocess
import argparse
import time
import threading
import shutil

# ANSI 颜色代码
class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
    ITALIC = '\033[3m'
    
    # 背景色
    BG_BLUE = '\033[44m'
    BG_GREEN = '\033[42m'
    BG_RED = '\033[41m'
    BG_YELLOW = '\033[43m'

# 进度条动画
class Spinner:
    def __init__(self):
        self.running = False
        self.spinner_thread = None
        self.message = ""
        
    def spin(self):
        symbols = ['⠋', '⠙', '⠹', '⠸', '⠼', '⠴', '⠦', '⠧', '⠇', '⠏']
        idx = 0
        while self.running:
            sys.stdout.write(f"\r{Colors.OKBLUE}{symbols[idx]} {self.message}{Colors.ENDC}")
            sys.stdout.flush()
            idx = (idx + 1) % len(symbols)
            time.sleep(0.1)
        sys.stdout.write("\r" + " " * (len(self.message) + 2) + "\r")
        sys.stdout.flush()
    
    def start(self, message="处理中..."):
        self.message = message
        self.running = True
        self.spinner_thread = threading.Thread(target=self.spin)
        self.spinner_thread.daemon = True
        self.spinner_thread.start()
    
    def stop(self):
        self.running = False
        if self.spinner_thread:
            self.spinner_thread.join()

# 百分比进度条类
class ProgressBar:
    def __init__(self, total=100, width=40):
        self.total = total
        self.width = width
        self.current = 0
        self.running = False
        self.progress_thread = None
    
    def update(self, value, message=""):
        self.current = value
        self.print_progress(message)
    
    def print_progress(self, message=""):
        # 计算进度百分比
        percent = min(int((self.current / self.total) * 100), 100)
        # 计算进度条长度
        filled_length = int(self.width * self.current / self.total)
        # 构建进度条
        bar = '█' * filled_length + '-' * (self.width - filled_length)
        # 输出进度条
        sys.stdout.write(f"\r{Colors.OKCYAN}[{Colors.OKGREEN}{bar}{Colors.OKCYAN}] {percent}% {message}{Colors.ENDC}")
        sys.stdout.flush()
    
    def start(self, message=""):
        self.running = True
        self.progress_thread = threading.Thread(target=self._animate, args=(message,))
        self.progress_thread.daemon = True
        self.progress_thread.start()
    
    def _animate(self, message=""):
        # 简单的动画，模拟进度更新
        stages = [
            "解析笔记本结构...",
            "处理单元格内容...",
            "转换为HTML格式...",
            "应用样式和主题...",
            "渲染PDF页面...",
            "优化文件大小..."
        ]
        
        stage_idx = 0
        while self.running and self.current < self.total:
            # 模拟进度增加
            increment = min(5 + int(self.current / 20), 10)
            self.current = min(self.current + increment, self.total)
            
            # 每15%切换一次消息
            if self.current // 15 > stage_idx and stage_idx < len(stages):
                stage_idx += 1
            
            current_message = stages[stage_idx - 1] if stage_idx > 0 else message
            self.print_progress(current_message)
            time.sleep(0.3)  # 调整更新频率
    
    def stop(self):
        self.running = False
        if self.progress_thread:
            self.progress_thread.join()
        # 确保显示100%
        self.update(self.total, "转换完成！")
        print()

# 清屏函数
def clear_screen():
    """清屏函数"""
    os.system('cls' if os.name == 'nt' else 'clear')

# 打印带颜色的分隔线
def print_separator(length=60, char='=', color=Colors.OKCYAN):
    """打印带颜色的分隔线"""
    print(f"{color}{char * length}{Colors.ENDC}")

# 打印美化的标题
def print_header():
    """打印美化的程序头部信息"""
    clear_screen()
    
    # 中文标题
    title = f"{Colors.BOLD}{Colors.HEADER}"
    title += "     ╔══════════════════════════════════════════════════════╗     \n"
    title += "     ║                                                      ║     \n"
    title += "     ║                   Jupyter Notebook 转换               ║     \n"
    title += "     ║                                                      ║     \n"
    title += "     ║                     到 PDF 文档                       ║     \n"
    title += "     ║                                                      ║     \n"
    title += "     ║                      交互式工具                       ║     \n"
    title += "     ║                                                      ║     \n"
    title += "     ╚══════════════════════════════════════════════════════╝     \n"
    title += f"{Colors.ENDC}"
    
    subtitle = f"{Colors.BOLD}{Colors.OKBLUE}Linux 版本 v2.0{Colors.ENDC}\n"
    subtitle += f"{Colors.ITALIC}本工具将引导您完成 Jupyter Notebook 到 PDF 的转换过程{Colors.ENDC}"
    
    print(title)
    print(subtitle)
    print_separator()

# 获取输入的 ipynb 文件路径
def get_input_file():
    """获取输入的 ipynb 文件路径"""
    while True:
        prompt = f"{Colors.BOLD}{Colors.OKCYAN}请输入需要转换的 Jupyter Notebook 文件绝对路径{Colors.ENDC}: {Colors.ENDC}"
        file_path = input(prompt).strip()
        
        # 处理可能的引号
        if file_path.startswith(('"', "'")) and file_path.endswith(('"', "'")):
            file_path = file_path[1:-1]
        
        if os.path.exists(file_path):
            if file_path.lower().endswith('.ipynb'):
                print(f"{Colors.OKGREEN}✓ 文件有效: {file_path}{Colors.ENDC}")
                return file_path
            else:
                print(f"{Colors.FAIL}✗ 错误：文件 '{file_path}' 不是 .ipynb 文件{Colors.ENDC}")
        else:
            # 尝试相对路径
            rel_path = os.path.join(os.getcwd(), file_path)
            if os.path.exists(rel_path) and rel_path.lower().endswith('.ipynb'):
                print(f"{Colors.OKGREEN}✓ 文件有效: {rel_path}{Colors.ENDC}")
                return rel_path
            print(f"{Colors.FAIL}✗ 错误：找不到文件 '{file_path}'{Colors.ENDC}")

# 获取输出的 PDF 文件路径
def get_output_file(input_file):
    """获取输出的 PDF 文件路径"""
    default_output = os.path.splitext(input_file)[0] + '.pdf'
    prompt = f"{Colors.BOLD}{Colors.OKCYAN}请输入输出 PDF 文件路径{Colors.ENDC} [{default_output}，直接回车使用默认值]: {Colors.ENDC}"
    output_path = input(prompt).strip()
    
    if not output_path:
        print(f"{Colors.OKBLUE}✓ 使用默认输出路径: {default_output}{Colors.ENDC}")
        return default_output
    
    # 处理可能的引号
    if output_path.startswith(('"', "'")) and output_path.endswith(('"', "'")):
        output_path = output_path[1:-1]
    
    # 确保文件扩展名为 .pdf
    if not output_path.lower().endswith('.pdf'):
        output_path += '.pdf'
        print(f"{Colors.WARNING}! 已自动添加 .pdf 扩展名{Colors.ENDC}")
    
    # 确保输出目录存在
    output_dir = os.path.dirname(output_path)
    if output_dir and not os.path.exists(output_dir):
        try:
            spinner = Spinner()
            spinner.start(f"创建输出目录: {output_dir}")
            time.sleep(0.5)  # 给用户一些视觉反馈
            os.makedirs(output_dir)
            spinner.stop()
            print(f"{Colors.OKGREEN}✓ 已创建输出目录: {output_dir}{Colors.ENDC}")
        except Exception as e:
            print(f"{Colors.FAIL}✗ 错误：无法创建输出目录 '{output_dir}': {str(e)}{Colors.ENDC}")
            return default_output
    
    return output_path

# 获取纸张大小
def get_paper_size():
    """获取纸张大小"""
    valid_sizes = ['A3', 'A4', 'Letter', 'Legal']
    while True:
        prompt = f"{Colors.BOLD}{Colors.OKCYAN}请选择纸张大小{Colors.ENDC} [{valid_sizes[0]}，直接回车使用默认值，可选值: {', '.join(valid_sizes)}]: {Colors.ENDC}"
        size = input(prompt).strip()
        if not size:
            print(f"{Colors.OKBLUE}✓ 使用默认纸张大小: {valid_sizes[0]}{Colors.ENDC}")
            return valid_sizes[0]
        if size.upper() in valid_sizes:
            print(f"{Colors.OKGREEN}✓ 已选择纸张大小: {size.upper()}{Colors.ENDC}")
            return size.upper()
        
        # 显示无效选项的错误信息
        error_msg = f"{Colors.FAIL}✗ 无效的纸张大小。请选择以下之一:{Colors.ENDC} "
        for i, s in enumerate(valid_sizes):
            if i < len(valid_sizes) - 1:
                error_msg += f"{Colors.OKCYAN}{s}{Colors.ENDC}, "
            else:
                error_msg += f"{Colors.OKCYAN}或 {s}{Colors.ENDC}"
        print(error_msg)

# 获取页面方向
def get_orientation():
    """获取页面方向"""
    valid_orientations = ['portrait', 'landscape']
    while True:
        prompt = f"{Colors.BOLD}{Colors.OKCYAN}请选择页面方向{Colors.ENDC} [{valid_orientations[0]}，直接回车使用默认值，可选值: {', '.join(valid_orientations)}]: {Colors.ENDC}"
        orientation = input(prompt).strip()
        if not orientation:
            print(f"{Colors.OKBLUE}✓ 使用默认页面方向: {valid_orientations[0]}{Colors.ENDC}")
            return valid_orientations[0]
        if orientation.lower() in valid_orientations:
            print(f"{Colors.OKGREEN}✓ 已选择页面方向: {orientation.lower()}{Colors.ENDC}")
            return orientation.lower()
        print(f"{Colors.FAIL}✗ 错误：无效的页面方向。请选择 '{Colors.OKCYAN}portrait{Colors.ENDC}' 或 '{Colors.OKCYAN}landscape{Colors.ENDC}'{Colors.ENDC}")

# 打印进度信息
def print_progress(stage, message):
    """打印带颜色的进度信息"""
    stages = {
        'start': Colors.OKBLUE,
        'converting': Colors.WARNING,
        'success': Colors.OKGREEN,
        'error': Colors.FAIL
    }
    color = stages.get(stage, Colors.ENDC)
    print(f"{color}{message}{Colors.ENDC}")

# 运行转换程序
def run_conversion(input_file, output_file, paper_size, orientation):
    """运行转换程序"""
    # 获取当前脚本所在目录
    script_dir = os.path.dirname(os.path.abspath(__file__))
    converter_path = os.path.join(script_dir, 'ipynb_to_pdf_converter.py')
    
    # 确保转换程序存在
    if not os.path.exists(converter_path):
        print(f"{Colors.FAIL}✗ 错误：找不到转换程序 '{converter_path}'{Colors.ENDC}")
        return False
    
    # 构建命令参数
    cmd = [
        sys.executable,
        converter_path,
        input_file,
        '--output', output_file,
        '--paper', paper_size,
        '--orientation', orientation
    ]
    
    print_separator()
    print(f"{Colors.BOLD}{Colors.OKCYAN}开始转换过程{Colors.ENDC}")
    print_separator(char='-')
    print(f"{Colors.OKBLUE}📄 输入文件: {input_file}{Colors.ENDC}")
    print(f"{Colors.OKBLUE}📑 输出文件: {output_file}{Colors.ENDC}")
    print(f"{Colors.OKBLUE}📏 纸张大小: {paper_size}{Colors.ENDC}")
    print(f"{Colors.OKBLUE}🔄 页面方向: {orientation}{Colors.ENDC}")
    print_separator(char='-')
    
    # 创建并启动加载动画
    spinner = Spinner()
    spinner.start("正在准备转换环境...")
    
    try:
        # 短暂延迟以显示动画
        time.sleep(1)
        spinner.stop()
        
        print_progress('start', "🚀 开始转换，这可能需要几分钟时间...")
        
        # 运行转换命令
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            universal_newlines=True,
            encoding='utf-8'
        )
        
        # 创建百分比进度条
        progress_bar = ProgressBar()
        progress_bar.start()
        
        # 实时显示输出
        last_stage = ""
        for line in process.stdout:
            line = line.strip()
            if line:
                # 根据输出内容更新进度条
                if "临时HTML文件" in line:
                    progress_bar.update(30)  # 30% 进度
                    print(f"{Colors.OKBLUE}🔧 {line}{Colors.ENDC}")
                elif "生成PDF" in line:
                    progress_bar.update(60)  # 60% 进度
                    print(f"{Colors.OKBLUE}📊 {line}{Colors.ENDC}")
                elif "已生成" in line:
                    progress_bar.update(90)  # 90% 进度
                    print(f"{Colors.OKGREEN}✅ {line}{Colors.ENDC}")
                elif "已清理" in line:
                    progress_bar.update(95)  # 95% 进度
                    print(f"{Colors.OKGREEN}🧹 {line}{Colors.ENDC}")
                else:
                    print(line)
        
        # 完成进度条
        progress_bar.stop()
        process.wait()
        
        print_separator(char='-')
        if process.returncode == 0:
            print_progress('success', "🎉 转换成功完成！")
            if os.path.exists(output_file):
                file_size = os.path.getsize(output_file) / (1024 * 1024)
                print(f"{Colors.OKGREEN}📁 PDF 文件大小: {file_size:.2f} MB{Colors.ENDC}")
            return True
        else:
            print_progress('error', f"❌ 转换失败，返回码: {process.returncode}")
            return False
            
    except Exception as e:
        if 'progress_bar' in locals():
            progress_bar.stop()
        else:
            spinner.stop()
        print_progress('error', f"❌ 转换过程中发生错误: {str(e)}")
        return False

# 显示参数确认框
def show_confirmation(input_file, output_file, paper_size, orientation):
    """显示美化的参数确认框"""
    print()
    print(f"{Colors.BOLD}{Colors.OKCYAN}╔{'═' * 58}╗{Colors.ENDC}")
    print(f"{Colors.BOLD}{Colors.OKCYAN}║{'转换参数确认':^58}║{Colors.ENDC}")
    print(f"{Colors.BOLD}{Colors.OKCYAN}╠{'═' * 58}╣{Colors.ENDC}")
    
    # 格式化输出，使各部分对齐
    max_label_len = 8
    input_label = f"输入文件:".ljust(max_label_len)
    output_label = f"输出文件:".ljust(max_label_len)
    paper_label = f"纸张大小:".ljust(max_label_len)
    orientation_label = f"页面方向:".ljust(max_label_len)
    
    print(f"{Colors.OKCYAN}║ {input_label} {Colors.ENDC}{input_file[:48]}{'...' if len(input_file) > 48 else ''}{Colors.OKCYAN} {' ' * (58 - max_label_len - len(input_file[:48]) - (3 if len(input_file) > 48 else 0))} ║{Colors.ENDC}")
    print(f"{Colors.OKCYAN}║ {output_label} {Colors.ENDC}{output_file[:48]}{'...' if len(output_file) > 48 else ''}{Colors.OKCYAN} {' ' * (58 - max_label_len - len(output_file[:48]) - (3 if len(output_file) > 48 else 0))} ║{Colors.ENDC}")
    print(f"{Colors.OKCYAN}║ {paper_label} {Colors.ENDC}{paper_size}{Colors.OKCYAN} {' ' * (58 - max_label_len - len(paper_size))} ║{Colors.ENDC}")
    print(f"{Colors.OKCYAN}║ {orientation_label} {Colors.ENDC}{orientation}{Colors.OKCYAN} {' ' * (58 - max_label_len - len(orientation))} ║{Colors.ENDC}")
    print(f"{Colors.BOLD}{Colors.OKCYAN}╚{'═' * 58}╝{Colors.ENDC}")
    
    # 确认提示 - 添加默认值为y
    prompt = f"{Colors.BOLD}{Colors.WARNING}🔍 确认开始转换? (y/n) [默认: y]: {Colors.ENDC}"
    confirm = input(prompt).strip().lower()
    # 如果用户直接回车，默认为y
    if not confirm:
        return True
    return confirm == 'y'

# 主函数
def main():
    """主函数"""
    try:
        print_header()
        
        # 检查依赖
        spinner = Spinner()
        spinner.start("检查必要的 Python 依赖...")
        
        try:
            import nbconvert
            import playwright
            spinner.stop()
            print(f"{Colors.OKGREEN}✅ 已安装必要的 Python 依赖{Colors.ENDC}")
        except ImportError:
            spinner.stop()
            print(f"{Colors.WARNING}⚠️  警告：未检测到所有必要的依赖。{Colors.ENDC}")
            print(f"{Colors.ITALIC}  建议运行: pip install nbconvert playwright pandas jupyter matplotlib seaborn{Colors.ENDC}")
            print(f"{Colors.ITALIC}  以及: playwright install chromium{Colors.ENDC}")
            input(f"{Colors.OKCYAN}  按回车键继续...{Colors.ENDC}")
        
        print_separator()
        
        # 获取用户输入
        input_file = get_input_file()
        output_file = get_output_file(input_file)
        paper_size = get_paper_size()
        orientation = get_orientation()
        
        # 确认参数
        if not show_confirmation(input_file, output_file, paper_size, orientation):
            print(f"{Colors.WARNING}🛑 转换已取消。{Colors.ENDC}")
            return
        
        # 执行转换
        success = run_conversion(input_file, output_file, paper_size, orientation)
        
        # 转换完成后的提示
        print_separator()
        if success:
            print(f"{Colors.BG_GREEN} {Colors.BOLD}✓ 转换完成！PDF 文件已保存至: {output_file} {Colors.ENDC}")
        else:
            print(f"{Colors.BG_RED} {Colors.BOLD}✗ 转换失败，请检查错误信息并尝试解决问题。 {Colors.ENDC}")
        
        # 询问是否继续转换其他文件
        print()
        prompt = f"{Colors.BOLD}{Colors.OKCYAN}🔄 是否继续转换其他文件? (y/n) [默认: n]: {Colors.ENDC}"
        again = input(prompt).strip().lower()
        if again == 'y':
            main()
        else:
            print()
            print(f"{Colors.BOLD}{Colors.HEADER}感谢使用 Jupyter Notebook 到 PDF 转换工具！{Colors.ENDC}")
            print(f"{Colors.ITALIC}祝您工作顺利！{Colors.ENDC}")
            print_separator()
            
    except KeyboardInterrupt:
        print(f"\n{Colors.WARNING}👋 程序已被用户中断。{Colors.ENDC}")
    except Exception as e:
        print(f"\n{Colors.FAIL}❌ 程序运行出错: {str(e)}{Colors.ENDC}")
        import traceback
        traceback.print_exc()
    finally:
        input(f"\n{Colors.OKCYAN}👋 按回车键退出程序...{Colors.ENDC}")

if __name__ == "__main__":
    main()
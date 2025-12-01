#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Jupyter Notebook 到 PDF 转换工具
支持中文、英文、特殊符号、数学公式、在线图片和粘贴图片
纸张大小：A3 竖版
"""

import os
import sys
import json
import base64
from pathlib import Path
import argparse
import tempfile
import shutil
from concurrent.futures import ThreadPoolExecutor

import nbformat
from nbconvert import HTMLExporter
from playwright.sync_api import sync_playwright

class IPYNBtoPDFConverter:
    """Jupyter Notebook 到 PDF 转换类"""
    
    def __init__(self, input_file, output_file=None, paper_size="A3", orientation="portrait"):
        """
        初始化转换器
        
        Args:
            input_file: 输入的ipynb文件路径
            output_file: 输出的pdf文件路径，默认为同目录下同名pdf
            paper_size: 纸张大小，默认为A3
            orientation: 纸张方向，portrait(竖版)或landscape(横版)
        """
        self.input_file = Path(input_file)
        if not self.input_file.exists():
            raise FileNotFoundError(f"找不到输入文件: {input_file}")
        
        # 设置输出文件路径
        if output_file:
            self.output_file = Path(output_file)
        else:
            self.output_file = self.input_file.with_suffix('.pdf')
        
        # 确保输出目录存在
        self.output_file.parent.mkdir(parents=True, exist_ok=True)
        
        self.paper_size = paper_size
        self.orientation = orientation
        self.temp_dir = None
    
    def extract_embedded_images(self, notebook_content):
        """
        提取notebook中嵌入的base64编码图片并保存到临时目录
        
        Args:
            notebook_content: 解析后的notebook内容
        
        Returns:
            处理后的notebook内容（更新图片引用）
        """
        if not self.temp_dir:
            self.temp_dir = tempfile.mkdtemp()
        
        image_dir = Path(self.temp_dir) / "images"
        image_dir.mkdir(exist_ok=True)
        
        # 遍历所有单元格
        for cell in notebook_content.cells:
            if cell.cell_type == 'markdown' or cell.cell_type == 'code':
                if 'outputs' in cell:
                    for output in cell.outputs:
                        if 'data' in output:
                            data = output['data']
                            # 处理base64编码的图片
                            for mime_type in ['image/png', 'image/jpeg', 'image/jpg']:
                                if mime_type in data:
                                    image_data = data[mime_type]
                                    if isinstance(image_data, str):
                                        # 创建唯一的图片文件名
                                        import hashlib
                                        img_hash = hashlib.md5(image_data.encode()).hexdigest()
                                        img_ext = mime_type.split('/')[1]
                                        img_filename = f"embedded_{img_hash}.{img_ext}"
                                        img_path = image_dir / img_filename
                                        
                                        # 保存图片
                                        with open(img_path, 'wb') as f:
                                            f.write(base64.b64decode(image_data))
                                        
                                        # 更新output数据，将base64数据替换为文件引用
                                        # 注意：这不会修改原始的JSON结构，因为我们只在转换为HTML时处理
        
        return notebook_content
    
    def convert_to_html(self):
        """
        将ipynb转换为HTML文件
        
        Returns:
            HTML文件路径
        """
        if not self.temp_dir:
            self.temp_dir = tempfile.mkdtemp()
        
        # 读取notebook文件
        with open(self.input_file, 'r', encoding='utf-8') as f:
            notebook = nbformat.read(f, as_version=4)
        
        # 提取嵌入图片
        notebook = self.extract_embedded_images(notebook)
        
        # 创建HTML导出器
        html_exporter = HTMLExporter()
        html_exporter.template_name = 'classic'
        
        # 配置HTML导出选项
        html_exporter.exclude_input_prompts = False
        html_exporter.exclude_output_prompts = False
        html_exporter.exclude_output = False
        html_exporter.embed_images = False  # 不嵌入图片，使用外部文件引用
        
        # 导出HTML
        (body, resources) = html_exporter.from_notebook_node(notebook)
        
        # 添加自定义CSS以确保中文显示和A3纸张格式
        custom_css = """
        <style>
            @font-face {
                font-family: 'Computer Modern';
                src: local('Computer Modern'), local('CMU Serif');
            }
            body {
                font-family: 'Computer Modern', 'Times New Roman', serif;
                font-size: 12pt;
                line-height: 1.6;
                margin: 0;
                padding: 0;
                color: #000000;
                background-color: #ffffff;
            }
            .container {
                max-width: 100%;
                margin: 0;
                padding: 2cm;
                box-sizing: border-box;
            }
            /* 确保代码块显示正常 */
            pre, code {
                font-family: 'Courier New', Courier, monospace;
                background-color: #f5f5f5;
                border-radius: 3px;
                padding: 0.2em 0.4em;
            }
            pre {
                padding: 1em;
                overflow-x: auto;
            }
            /* 确保公式显示正常 */
            .MathJax {
                font-size: 115% !important;
            }
            /* 调整标题样式 */
            h1, h2, h3, h4, h5, h6 {
                color: #000000;
                margin-top: 1.5em;
                margin-bottom: 0.5em;
            }
            /* 确保表格显示正常 */
            table {
                border-collapse: collapse;
                width: 100%;
                margin-bottom: 1em;
            }
            th, td {
                border: 1px solid #ddd;
                padding: 8px;
                text-align: left;
            }
            th {
                background-color: #f2f2f2;
            }
            /* 确保图片正确缩放 */
            img {
                max-width: 100%;
                height: auto;
                margin: 1em 0;
            }
            /* 修复某些组件的显示问题 */
            .output {
                margin-top: 1em;
                padding: 1em;
                border: 1px solid #eee;
                border-radius: 4px;
            }
            /* 防止页面内容溢出 */
            .output_area {
                overflow-x: auto;
            }
        </style>
        """
        
        # 将自定义CSS添加到HTML头部
        if '<head>' in body:
            body = body.replace('<head>', f'<head>{custom_css}')
        else:
            body = f"{custom_css}{body}"
        
        # 保存HTML文件
        html_path = Path(self.temp_dir) / f"{self.input_file.stem}.html"
        with open(html_path, 'w', encoding='utf-8') as f:
            f.write(body)
        
        # 复制资源文件（如嵌入的图片）
        if 'outputs' in resources:
            for key, value in resources['outputs'].items():
                output_path = Path(self.temp_dir) / key
                with open(output_path, 'wb') as f:
                    f.write(value)
        
        return html_path
    
    def html_to_pdf(self, html_path):
        """
        使用Playwright将HTML转换为PDF
        
        Args:
            html_path: HTML文件路径
        """
        # 将路径转换为file:// URL
        html_url = f"file://{html_path.resolve()}"
        
        # 使用Playwright将HTML转换为PDF
        with sync_playwright() as p:
            # 启动Chromium
            browser = p.chromium.launch(
                headless=True,
                args=[
                    '--disable-gpu',
                    '--disable-dev-shm-usage',
                    '--disable-setuid-sandbox',
                    '--no-sandbox'
                ]
            )
            
            # 创建新页面
            page = browser.new_page(
                viewport={'width': 1920, 'height': 1080},
                # 设置支持中文的用户代理
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            )
            
            # 导航到HTML文件
            page.goto(html_url, wait_until='networkidle')
            
            # 等待所有内容加载完成，特别是数学公式
            page.wait_for_timeout(2000)  # 等待2秒确保内容加载
            
            # 获取页面高度以确保捕获所有内容
            page.evaluate("""
                () => {
                    // 确保所有图片都已加载
                    const images = document.querySelectorAll('img');
                    const promises = Array.from(images).map(img => {
                        if (img.complete) return Promise.resolve();
                        return new Promise(resolve => {
                            img.onload = resolve;
                            img.onerror = resolve; // 即使图片加载失败也继续
                        });
                    });
                    return Promise.all(promises);
                }
            """)
            
            # 设置PDF选项
            pdf_options = {
                'path': str(self.output_file),
                'format': self.paper_size.lower(),
                'landscape': self.orientation.lower() == 'landscape',
                'print_background': True,
                'margin': {
                    'top': '2cm',
                    'right': '2cm',
                    'bottom': '2cm',
                    'left': '2cm'
                },
                # 确保字体嵌入以支持中文显示
                'prefer_css_page_size': True
            }
            
            # 生成PDF
            page.pdf(**pdf_options)
            
            # 关闭浏览器
            browser.close()
    
    def convert(self):
        """
        执行完整的转换流程
        """
        try:
            print(f"开始转换: {self.input_file}")
            print(f"输出路径: {self.output_file}")
            
            # 1. 转换为HTML
            html_path = self.convert_to_html()
            print(f"已生成临时HTML文件: {html_path}")
            
            # 2. HTML转换为PDF
            print("正在使用Playwright生成PDF...")
            self.html_to_pdf(html_path)
            print(f"PDF文件已生成: {self.output_file}")
            
            return True
        
        except Exception as e:
            print(f"转换失败: {str(e)}")
            import traceback
            traceback.print_exc()
            return False
        
        finally:
            # 清理临时文件
            if self.temp_dir and Path(self.temp_dir).exists():
                try:
                    shutil.rmtree(self.temp_dir)
                    print(f"已清理临时文件: {self.temp_dir}")
                except Exception as e:
                    print(f"清理临时文件失败: {str(e)}")

def main():
    """
    主函数，处理命令行参数并执行转换
    """
    parser = argparse.ArgumentParser(description='Jupyter Notebook 到 PDF 转换工具')
    parser.add_argument('input_file', help='输入的Jupyter Notebook文件路径')
    parser.add_argument('-o', '--output_file', help='输出的PDF文件路径（可选）')
    parser.add_argument('--paper', default='A3', help='纸张大小，默认为A3')
    parser.add_argument('--orientation', default='portrait', choices=['portrait', 'landscape'],
                        help='纸张方向，portrait(竖版)或landscape(横版)，默认为竖版')
    
    args = parser.parse_args()
    
    # 创建转换器实例
    converter = IPYNBtoPDFConverter(
        input_file=args.input_file,
        output_file=args.output_file,
        paper_size=args.paper,
        orientation=args.orientation
    )
    
    # 执行转换
    success = converter.convert()
    
    # 根据转换结果设置退出码
    sys.exit(0 if success else 1)

if __name__ == '__main__':
    main()
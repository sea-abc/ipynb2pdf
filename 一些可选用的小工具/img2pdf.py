import os
import re
import math
import argparse
from PIL import Image
from reportlab.lib.pagesizes import A4, A3, A5, landscape
from reportlab.pdfgen import canvas
from reportlab.lib.units import mm
from reportlab.lib.utils import ImageReader

# 超参数配置
PDF_MARGIN_LEFT = 15  # PDF左侧空隙（mm）
PDF_MARGIN_RIGHT = 15  # PDF右侧空隙（mm）
PDF_MARGIN_TOP = 0  # PDF顶部空隙（mm）
PDF_MARGIN_BOTTOM = 0  # PDF底部空隙（mm） #注意这里还是会有取整等误差的，所以不能完全贴合，除非切片数量足够多，但会影响图片质量
PDF_PAGE_SIZE = A4  # PDF页面大小选项：A4, A3, A5, 或 landscape(A4), landscape(A3), landscape(A5)
#INPUT_FOLDER = r"C:\Users\53108\Desktop\开发inbpy转pdf项目\test"  # 输入图片文件夹路径(测试用的)
#OUTPUT_PDF = r"C:\Users\53108\Desktop\开发inbpy转pdf项目\test\test.pdf"  # 输出PDF文件名(测试用的)
INPUT_FOLDER = r"E:\Python_materials\大模型原理正课\part3 deepseek及其预训练\deepseekv3原理"  # 输入图片文件夹路径
OUTPUT_PDF = r"E:\Python_materials\大模型原理正课\part3 deepseek及其预训练\deepseekv3原理\deepseekv3.pdf"  # 输出PDF文件名
USER_SPECIFIED_SLICES = 3500  # 用户指定的切片数量（可选，设置为整数或None自动计算）



def read_image(image_path):
    """
    读取图片文件
    :param image_path: 图片文件路径
    :return: PIL.Image对象
    """
    try:
        img = Image.open(image_path)
        # 确保图片为RGB模式
        if img.mode != 'RGB':
            img = img.convert('RGB')
        return img
    except Exception as e:
        print(f"读取图片失败 {image_path}: {e}")
        return None


def merge_images(images):
    """
    将所有图片按顺序合并成一个长图（不缩放）
    :param images: PIL.Image对象列表
    :return: 合并后的长图
    """
    if not images:
        return None
    
    # 确保所有图片为RGB模式
    rgb_images = []
    for img in images:
        if img.mode != 'RGB':
            img = img.convert('RGB')
        rgb_images.append(img)
    
    # 计算合并后的长图尺寸（宽度取所有图片的最大宽度，高度累加）
    max_width = max(img.width for img in rgb_images)
    total_height = sum(img.height for img in rgb_images)
    
    # 创建合并后的长图（使用白色背景）
    merged_img = Image.new('RGB', (max_width, total_height), color=(255, 255, 255))
    
    # 将所有图片粘贴到长图中（从上到下顺序，居中对齐）
    current_y = 0
    for idx, img in enumerate(rgb_images):
        img_width, img_height = img.size
        print(f"  图片 {idx+1} 尺寸: {img_width}px × {img_height}px")
        
        # 居中对齐（左右居中）
        x_offset = (max_width - img_width) // 2
        merged_img.paste(img, (x_offset, current_y))
        current_y += img_height
    
    print(f"合并后的长图尺寸: {merged_img.width}px × {merged_img.height}px")
    return merged_img


def calculate_scaled_size(merged_img, pdf_width_mm):
    """
    计算长图在宽铺满PDF时的尺寸
    :param merged_img: 合并后的长图
    :param pdf_width_mm: PDF页面宽度（mm）
    :return: 缩放后的长图，缩放比例
    """
    # 使用300dpi作为PDF的标准分辨率
    dpi = 300
    
    # 计算PDF页面的有效宽度（减去左右空隙）
    available_pdf_width_mm = pdf_width_mm - PDF_MARGIN_LEFT - PDF_MARGIN_RIGHT
    # 转换为像素
    target_width_px = int(round(available_pdf_width_mm * dpi / 25.4))
    
    print(f"PDF页面宽度: {pdf_width_mm:.2f}mm")
    print(f"两侧空隙: 左 {PDF_MARGIN_LEFT}mm + 右 {PDF_MARGIN_RIGHT}mm = {PDF_MARGIN_LEFT + PDF_MARGIN_RIGHT}mm")
    print(f"图片目标宽度: {target_width_px}px (将铺满PDF有效区域)")
    
    # 计算缩放比例
    scale_ratio = target_width_px / max(1, merged_img.width)
    print(f"缩放比例: {scale_ratio:.4f}")
    
    # 计算缩放后的尺寸
    scaled_width = int(round(merged_img.width * scale_ratio))
    scaled_height = int(round(merged_img.height * scale_ratio))
    
    # 确保缩放后的尺寸至少为1像素
    scaled_width = max(1, scaled_width)
    scaled_height = max(1, scaled_height)
    
    # 使用高质量的缩放算法
    scaled_img = merged_img.resize((scaled_width, scaled_height), Image.LANCZOS)
    print(f"📏 缩放后的长图尺寸: {scaled_width}px × {scaled_height}px")
    
    return scaled_img, scale_ratio


def calculate_min_slices(scaled_img, pdf_height_mm):
    """
    计算最少需要的切片数量
    :param scaled_img: 缩放后的长图
    :param pdf_height_mm: PDF页面高度（mm）
    :return: 最少切片数量
    """
    # 使用300dpi作为PDF的标准分辨率
    dpi = 300
    
    # 计算PDF页面的有效高度（减去上下空隙）
    available_pdf_height_mm = pdf_height_mm - PDF_MARGIN_TOP - PDF_MARGIN_BOTTOM
    # 转换为像素
    available_height_px = int(round(available_pdf_height_mm * dpi / 25.4))
    
    print(f"PDF页面高度: {pdf_height_mm:.2f}mm")
    print(f"上下空隙: 上 {PDF_MARGIN_TOP}mm + 下 {PDF_MARGIN_BOTTOM}mm = {PDF_MARGIN_TOP + PDF_MARGIN_BOTTOM}mm")
    print(f"每页最大图片高度: {available_height_px}px (将完整显示在PDF页面中)")
    
    # 计算最少需要的切片数量
    min_slices = max(1, int(math.ceil(scaled_img.height / available_height_px)))
    print(f"🔢 最少需要的切片数量: {min_slices}")
    
    return min_slices


def split_image(merged_img, num_slices):
    """
    将长图按高的方向切分成若干个小图
    :param merged_img: 合并并缩放后的长图
    :param num_slices: 切片数量
    :return: 切片列表
    """
    if not merged_img or num_slices <= 0:
        return []
    
    img_width_px, img_height_px = merged_img.size
    print(f"将长图切分成 {num_slices} 个小图")
    
    # 计算每个切片的高度（确保切片高度尽可能均匀）
    slice_height = img_height_px // num_slices
    remainder = img_height_px % num_slices
    print(f"每个切片的高度: {slice_height}px (最后一个切片会多出 {remainder}px)")
    
    # 切分长图
    slices = []
    current_top = 0
    
    for i in range(num_slices):
        # 计算切片的顶部和底部位置
        top = current_top
        
        # 分配剩余高度
        if i == num_slices - 1:
            bottom = img_height_px
        else:
            bottom = top + slice_height + (1 if i < remainder else 0)
        
        # 裁剪切片
        slice_img = merged_img.crop((0, top, img_width_px, bottom))
        slices.append(slice_img)
        
        print(f"  切片 {i+1}: 顶部 {top}px - 底部 {bottom}px, 尺寸: {slice_img.width}px × {slice_img.height}px")
        
        # 更新当前顶部位置
        current_top = bottom
    
    return slices

def create_pdf(slices, output_path):
    """
    创建PDF文件并插入图片切片
    :param slices: 图片切片列表
    :param output_path: 输出PDF文件路径
    :return: 生成的PDF页数
    """
    if not slices:
        print("错误：没有可处理的图片切片")
        return 0
    
    print("正在将图片切片添加到PDF中...")
    
    # 使用指定的页面大小
    page_width, page_height = PDF_PAGE_SIZE
    print(f"PDF页面尺寸: {page_width}pt × {page_height}pt")
    
    # 创建PDF画布
    c = canvas.Canvas(output_path, pagesize=PDF_PAGE_SIZE)
    
    # 将mm转换为点（reportlab的单位）
    margin_left_pt = PDF_MARGIN_LEFT * mm
    margin_right_pt = PDF_MARGIN_RIGHT * mm
    margin_top_pt = PDF_MARGIN_TOP * mm
    margin_bottom_pt = PDF_MARGIN_BOTTOM * mm
    print(f"PDF边界: 左 {PDF_MARGIN_LEFT}mm, 右 {PDF_MARGIN_RIGHT}mm, 上 {PDF_MARGIN_TOP}mm, 下 {PDF_MARGIN_BOTTOM}mm")
    
    # 计算PDF中图片的可用尺寸
    available_width_pt = page_width - margin_left_pt - margin_right_pt
    available_height_pt = page_height - margin_top_pt - margin_bottom_pt
    print(f"PDF中图片可用尺寸: {available_width_pt}pt × {available_height_pt}pt")
    
    # 开始绘制图片
    page_count = 1  # 页面计数
    current_y = page_height - margin_top_pt  # 当前页可用的顶部位置
    
    for slice_idx, slice_img in enumerate(slices):
        # 获取切片尺寸
        slice_width_px, slice_height_px = slice_img.size
        
        # 计算切片在PDF中的显示尺寸（宽度铺满可用区域）
        scale_ratio = available_width_pt / slice_width_px
        slice_width_pt = available_width_pt
        slice_height_pt = slice_height_px * scale_ratio
        
        print(f"\n处理切片 {slice_idx+1}:")
        print(f"  切片尺寸: {slice_width_px}px × {slice_height_px}px")
        print(f"  在PDF中的显示尺寸: {slice_width_pt:.2f}pt × {slice_height_pt:.2f}pt")
        
        # 检查当前页是否能容纳这个切片
        if current_y - slice_height_pt < margin_bottom_pt:
            # 页放不下，创建新页面
            c.showPage()
            page_count += 1
            current_y = page_height - margin_top_pt  # 重置当前页的顶部位置
            print(f"  当前页放不下，创建新页面 (PDF第 {page_count} 页)")
        
        # 计算切片在PDF中的位置
        x = margin_left_pt  # 左侧边距
        y = current_y - slice_height_pt  # 当前位置下方开始
        
        print(f"  在PDF中的位置: x={x:.2f}pt, y={y:.2f}pt (PDF第 {page_count} 页)")
        
        # 将图片转换为ImageReader
        img_reader = ImageReader(slice_img)
        
        # 绘制图片
        c.drawImage(img_reader, x, y, width=slice_width_pt, height=slice_height_pt, preserveAspectRatio=True, mask='auto')
        
        # 更新当前页可用的顶部位置
        current_y = y
    
    # 保存PDF文件
    c.save()
    print(f"\nPDF文件已成功保存到: {output_path}")
    return page_count


def get_sorted_images(folder_path):
    """
    从文件夹中获取按数字命名排序的图片列表
    :param folder_path: 图片文件夹路径
    :return: 图片文件路径列表
    """
    # 获取文件夹中所有图片文件
    image_files = []
    valid_extensions = ['.jpg', '.jpeg', '.png', '.bmp', '.gif']
    
    for file_name in os.listdir(folder_path):
        file_path = os.path.join(folder_path, file_name)
        if os.path.isfile(file_path):
            ext = os.path.splitext(file_name)[1].lower()
            if ext in valid_extensions:
                image_files.append(file_path)
    
    # 按文件名中的数字排序
    def sort_key(file_path):
        file_name = os.path.basename(file_path)
        # 提取文件名中的所有数字并组合成一个整数
        # 这样可以正确处理多位数的文件名，如 "10.jpg" 会排在 "2.jpg" 后面
        numbers = re.findall(r'\d+', file_name)
        if numbers:
            # 将所有数字组合成一个字符串，然后转换为整数
            return int(''.join(numbers))
        return 0
    
    sorted_files = sorted(image_files, key=sort_key)
    print(f"图片排序结果: {[os.path.basename(f) for f in sorted_files]}")
    return sorted_files


def main():
    """
    主函数
    """
    # 创建命令行参数解析器
    parser = argparse.ArgumentParser(description='将多张图片合并并转换为PDF文件')
    parser.add_argument('--slices', type=int, help='指定切片数量')
    args = parser.parse_args()
    
    print("开始处理图片...")
    print(f"输入文件夹: {INPUT_FOLDER}")
    print(f"输出PDF: {OUTPUT_PDF}")
    print(f"PDF页面大小: {PDF_PAGE_SIZE.__name__ if hasattr(PDF_PAGE_SIZE, '__name__') else PDF_PAGE_SIZE}")
    print(f"左边界: {PDF_MARGIN_LEFT}mm")
    print(f"右边界: {PDF_MARGIN_RIGHT}mm")
    print(f"上边界: {PDF_MARGIN_TOP}mm")
    print(f"下边界: {PDF_MARGIN_BOTTOM}mm")
    print()
    
    # 从文件夹获取按顺序排序的图片
    image_paths = get_sorted_images(INPUT_FOLDER)
    
    if not image_paths:
        print(f"错误: 在文件夹 {INPUT_FOLDER} 中没有找到可处理的图片")
        return
    
    # 读取所有输入图片
    images = []
    for image_path in image_paths:
        img = read_image(image_path)
        if img:
            images.append(img)
            print(f"已读取图片: {os.path.basename(image_path)}")
    
    if not images:
        print("错误: 没有可处理的图片")
        return
    
    print()
    
    # 计算PDF页面尺寸（转换为mm）
    page_width, page_height = PDF_PAGE_SIZE
    page_width_mm = page_width / mm
    page_height_mm = page_height / mm
    
    print(f"PDF页面尺寸: {page_width_mm:.2f}mm × {page_height_mm:.2f}mm")
    
    # 将所有图片合并
    print("正在合并所有图片...")
    merged_img = merge_images(images)
    
    if not merged_img:
        print("错误: 图片合并失败")
        return
    
    print(f"合并后的长图尺寸: {merged_img.width}px × {merged_img.height}px")
    print("图片合并完成！")
    print()
    
    # 计算长图在宽铺满PDF时的尺寸
    print("正在计算长图在宽铺满PDF时的尺寸...")
    scaled_img, scale_ratio = calculate_scaled_size(merged_img, page_width_mm)
    
    if not scaled_img:
        print("错误: 长图缩放失败")
        return
    
    print("长图尺寸计算完成！")
    print()
    
    # 计算最少需要的切片数量
    print("正在计算最少需要的切片数量...")
    min_slices = calculate_min_slices(scaled_img, page_height_mm)
    
    print("最少切片数量计算完成！")
    print()
    
    # 获取用户指定的切片数量
    num_slices = USER_SPECIFIED_SLICES
    
    # 优先使用命令行参数
    if args.slices is not None:
        num_slices = args.slices
    
    # 如果没有通过命令行参数指定，让用户交互式输入
    if num_slices is None:
        while True:
            try:
                print(f"🔢 最少需要的切片数量: {min_slices}")
                user_input = input(f"请输入切片数量 (不低于 {min_slices}): ")
                num_slices = int(user_input.strip())
                if num_slices >= min_slices:
                    break
                else:
                    print(f"⚠️  输入的切片数量小于最少需要的切片数量 {min_slices}")
                    print(f"将自动使用最少切片数量: {min_slices}")
                    num_slices = min_slices
                    break
            except ValueError:
                print("❌ 请输入有效的数字！")
                continue
    else:
        # 确保不低于最少切片数量
        if num_slices < min_slices:
            print(f"警告: 指定的切片数量 {num_slices} 小于最少需要的切片数量 {min_slices}")
            print(f"将使用最少切片数量: {min_slices}")
            num_slices = min_slices
    
    print(f"最终使用的切片数量: {num_slices}")
    print()
    
    # 切分长图
    print("正在切分长图...")
    slices = split_image(scaled_img, num_slices)
    
    if not slices:
        print("错误: 图片切分失败")
        return
    
    print("长图切分完成！")
    print()
    
    # 创建PDF
    print("正在生成PDF文件...")
    print("切片将依次添加到PDF中，确保图片内容完整显示")
    pdf_pages = create_pdf(slices, OUTPUT_PDF)
    
    print()
    print("✅ 处理完成！")
    print(f"📄 生成的PDF文件: {OUTPUT_PDF}")
    print(f"📁 输入图片文件夹: {INPUT_FOLDER}")
    print(f"📏 PDF页面大小: {PDF_PAGE_SIZE.__name__ if hasattr(PDF_PAGE_SIZE, '__name__') else PDF_PAGE_SIZE}")
    print(f"📐 边界设置: 左 {PDF_MARGIN_LEFT}mm, 右 {PDF_MARGIN_RIGHT}mm, 上 {PDF_MARGIN_TOP}mm, 下 {PDF_MARGIN_BOTTOM}mm")
    print(f"📷 处理的图片数量: {len(images)}")
    print(f"🔢 切片数量: {num_slices}")
    print(f"📄 PDF页数: {pdf_pages}")


if __name__ == "__main__":
    main()
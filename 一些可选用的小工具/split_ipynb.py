import json
import os
from typing import List

def count_cells(input_file: str) -> tuple[int, dict]:
    """
    统计ipynb文件的单元格数量，并验证文件有效性，返回单元格数和解析后的JSON数据
    
    参数：
        input_file: 输入的ipynb文件路径
    返回：
        单元格总数、解析后的Notebook JSON数据
    """
    # 检查文件存在性
    if not os.path.exists(input_file):
        raise FileNotFoundError(f"输入文件 {input_file} 不存在")
    # 检查文件格式
    if not input_file.endswith(".ipynb"):
        raise ValueError("输入文件必须是.ipynb格式的Jupyter Notebook文件")
    # 读取并解析JSON
    with open(input_file, "r", encoding="utf-8") as f:
        try:
            nb_data = json.load(f)
        except json.JSONDecodeError:
            raise ValueError("输入的ipynb文件不是有效的JSON格式，文件可能损坏")
    # 验证核心结构
    required_keys = ["cells", "nbformat", "nbformat_minor"]
    for key in required_keys:
        if key not in nb_data:
            raise KeyError(f"ipynb文件缺少核心字段 {key}，不是标准的Jupyter Notebook文件")
    return len(nb_data["cells"]), nb_data

def parse_custom_cells(input_str: str, total_cells: int) -> List[int]:
    """
    解析用户自定义的单元格数输入，返回整数列表，并做合法性校验
    
    参数：
        input_str: 用户输入的自定义字符串（如"5,3,4"）
        total_cells: 单元格总数
    返回：
        每个文件的单元格数列表
    """
    if not input_str.strip():
        return []
    
    # 将中文逗号转换为英文逗号
    input_str = input_str.replace("，", ",")
    
    # 检查是否以逗号结尾
    ends_with_comma = input_str.strip().endswith(",")
    
    # 按逗号分割并转换为整数
    try:
        custom_list = [int(num.strip()) for num in input_str.split(",") if num.strip()]
    except ValueError:
        raise ValueError("自定义数量必须是用逗号分隔的正整数（如5,3,4）")
    
    # 检查是否为正整数
    if any(num <= 0 for num in custom_list):
        raise ValueError("自定义的单元格数量必须是正整数")
    
    # 如果以逗号结尾且自定义列表不为空，添加一个0占位符表示将剩余单元格放入最后一个文件
    if ends_with_comma and custom_list:
        custom_list.append(0)
    
    # 计算已分配的总数
    assigned = sum(custom_list)
    if assigned > total_cells:
        print(f"⚠️  自定义数量总和（{assigned}）超过单元格总数（{total_cells}），将自动截断为总数！")
        return [min(num, total_cells - sum(custom_list[:i])) for i, num in enumerate(custom_list)]
    return custom_list

def calculate_distribution(total_cells: int, num_files: int = None, custom_cells: List[int] = None) -> List[int]:
    """
    计算单元格分配方案：优先自定义，无自定义则按文件数均分
    
    参数：
        total_cells: 单元格总数
        num_files: 均分模式下的文件数量
        custom_cells: 自定义模式下的单元格数列表
    返回：
        最终的单元格分配列表
    """
    # 自定义模式
    if custom_cells and len(custom_cells) > 0:
        assigned = sum(custom_cells)
        remaining = total_cells - assigned
        if remaining > 0:
            # 剩余单元格归入最后一个文件
            custom_cells[-1] += remaining
            print(f"⚠️  自定义数量总和（{assigned}）小于单元格总数（{total_cells}），剩余{remaining}个单元格归入最后一个文件")
        return custom_cells
    # 均分模式
    if num_files is None or num_files <= 0:
        raise ValueError("均分模式下文件数量必须是正整数")
    base = total_cells // num_files
    remainder = total_cells % num_files
    # 余数分配到前remainder个文件，每个多1个
    distribution = [base + 1 if i < remainder else base for i in range(num_files)]
    return distribution

def split_ipynb(nb_data: dict, distribution: List[int], output_dir: str = ".") -> None:
    """
    根据分配方案拆分ipynb文件并生成新文件
    
    参数：
        nb_data: 解析后的Notebook JSON数据
        distribution: 每个文件的单元格数分配列表
        output_dir: 输出目录
    """
    os.makedirs(output_dir, exist_ok=True)
    original_cells = nb_data["cells"]
    current_start = 0
    # 循环生成拆分后的文件
    for file_idx, cell_num in enumerate(distribution):
        if cell_num <= 0:
            continue
        current_end = current_start + cell_num
        # 防止索引越界
        current_end = min(current_end, len(original_cells))
        current_cells = original_cells[current_start:current_end]
        # 构建新的Notebook数据
        new_nb_data = {
            "cells": current_cells,
            "metadata": nb_data.get("metadata", {}),
            "nbformat": nb_data["nbformat"],
            "nbformat_minor": nb_data["nbformat_minor"]
        }
        # 生成输出文件路径
        output_file = os.path.join(output_dir, f"{file_idx + 1}.ipynb")
        # 写入文件
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(new_nb_data, f, ensure_ascii=False, indent=2)
        print(f"已生成：{output_file}（包含 {len(current_cells)} 个单元格）")
        current_start = current_end
    # 检查是否所有单元格都被拆分
    if current_start < len(original_cells):
        print(f"⚠️  有{len(original_cells) - current_start}个单元格未被拆分（分配方案可能有误）")

# 主程序入口
if __name__ == "__main__":
    try:
        # 第一步：输入文件路径并统计单元格
        input_file = input("请输入要拆分的ipynb文件路径（例如：test.ipynb）：").strip()
        # 去除可能存在的引号（单引号或双引号）
        if (input_file.startswith('"') and input_file.endswith('"')) or (input_file.startswith("'") and input_file.endswith("'")):
            input_file = input_file[1:-1]
        total_cells, nb_data = count_cells(input_file)
        print(f"\n✅ 成功读取文件，该Notebook共有 {total_cells} 个单元格")
        print(f"\n 目前Notebook单元格数的1/2约为 {total_cells // 2} 个单元格，\n 1/3约为 {total_cells // 3} 个单元格，\n 1/4约为 {total_cells // 4} 个单元格\n 1/5约为 {total_cells // 5} 个单元格，\n供参考")
        
        if total_cells == 0:
            print("📌 原文件无单元格，无需拆分！")
            exit()
        
        # 第二步：选择拆分模式（自定义/均分）
        custom_input = input("\n请输入每个文件的单元格数（用逗号分隔，如5,3,4；直接回车则进入均分模式）：").strip()
        distribution = []
        if custom_input:
            # 自定义模式
            custom_cells = parse_custom_cells(custom_input, total_cells)
            distribution = calculate_distribution(total_cells, custom_cells=custom_cells)
            # 显示当前文件分布情况
            print(f"\n📊 当前共分成了 {len(distribution)} 个文件，每个文件的单元格个数是：{distribution}")
        else:
            # 均分模式：输入拆分的文件数量
            while True:
                num_input = input(f"请输入要拆分成的文件数量（正整数，1-{total_cells}）：").strip()
                if not num_input.isdigit():
                    print("❌ 输入无效，请输入正整数！")
                    continue
                num_files = int(num_input)
                if 1 <= num_files <= total_cells:
                    break
                else:
                    print(f"❌ 输入无效，文件数量需在1-{total_cells}之间！")
            distribution = calculate_distribution(total_cells, num_files=num_files)
        
        # 第三步：输入输出目录
        output_dir = input("\n请输入输出目录（默认当前目录）：").strip()
        # 去除可能存在的引号（单引号或双引号）
        if (output_dir.startswith('"') and output_dir.endswith('"')) or (output_dir.startswith("'") and output_dir.endswith("'")):
            output_dir = output_dir[1:-1]
        output_dir = output_dir if output_dir else "."
        
        # 执行拆分
        print(f"\n📌 最终拆分分配方案：{distribution}")
        print("开始拆分...")
        split_ipynb(nb_data, distribution, output_dir)
        print("\n🎉 拆分完成！")
    
    except Exception as e:
        print(f"\n❌ 操作失败：{str(e)}")
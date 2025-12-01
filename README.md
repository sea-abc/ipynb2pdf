# Jupyter Notebook 到 PDF 转换工具 - Linux使用指南

## 文件夹内容说明

本文件夹包含在Linux环境中使用Jupyter Notebook转PDF工具所需的全部文件：

- `ipynb_to_pdf_converter.py` - 命令行版本的转换核心程序
- `interactive_converter.py` - 交互式引导程序（推荐使用）
- `README_LINUX.md` - 本使用指南

## Linux环境下的使用步骤

### 方法一：使用交互式引导程序（推荐）

1. **准备环境**
     - 确保您的Linux系统已安装Python 3.8或更高版本
     - 安装所有必要的依赖：
       方法A：使用 requirements.txt 文件（推荐）
       ```bash
       pip install -r requirements.txt
       playwright install chromium
       ```
       
       方法B：手动安装
       ```bash
       pip install nbconvert playwright pandas jupyter matplotlib seaborn
       playwright install chromium
       ```

2. **运行交互式程序**
   - 在终端中进入本文件夹
     ```bash
     cd /root/autodl-tmp/linux_deployment
     ```
   - 执行以下命令：
     ```bash
     python interactive_converter.py
     ```
   - 按照程序提示逐步输入：
     * 需要转换的Jupyter Notebook文件绝对路径
     * 输出PDF文件路径（可选，默认与输入文件同名）
     * 纸张大小（默认A3）
     * 页面方向（默认纵向portrait）

3. **查看转换结果**
   - 转换成功后，PDF文件将保存在您指定的路径
   - 程序会显示转换结果和文件大小信息

### 方法二：使用命令行直接转换

如果您更倾向于使用命令行直接转换，可以按照以下格式执行：

```bash
python ipynb_to_pdf_converter.py 输入文件路径 --output 输出文件路径 --paper 纸张大小 --orientation 页面方向
```

示例：
```bash
python ipynb_to_pdf_converter.py "/path/to/your/notebook.ipynb" --output "/path/to/output.pdf" --paper A3 --orientation portrait
```

## 支持的参数

- **纸张大小**：A3, A4, Letter, Legal
- **页面方向**：portrait（纵向）或landscape（横向）

## 注意事项

1. **文件路径**
   - 对于包含空格或特殊字符的文件路径，建议使用引号括起来
   - 对于中文文件名，本程序已优化处理，可正常识别和转换

2. **依赖安装**
   - 首次使用前，请确保所有依赖都已正确安装
   - Playwright需要下载Chromium浏览器，这可能需要一些时间

3. **权限问题**
   - 确保您对输入文件有读取权限，对输出目录有写入权限
   - 如果遇到权限错误，尝试使用sudo或以适当权限运行程序

4. **临时文件**
   - 转换过程中会生成临时HTML文件，转换完成后会自动清理
   - 确保您的系统有足够的临时存储空间

## 故障排除

1. **依赖错误**
   - 如果出现"找不到模块"错误，请检查所有依赖是否已正确安装
   - 尝试使用`pip install --upgrade`更新所有依赖包

2. **文件访问错误**
   - 检查文件路径是否正确
   - 确保您有足够的权限访问文件和目录

3. **PDF生成错误**
   - 如果转换失败，可能是因为Notebook内容过于复杂
   - 尝试简化Notebook内容或分批转换
   - 确保Chromium浏览器安装正确

## 系统要求

- Linux操作系统（已在Ubuntu、CentOS等主流发行版测试）
- Python 3.8或更高版本
- 至少500MB可用磁盘空间
- 互联网连接（用于安装依赖和Chromium）

祝您使用愉快！

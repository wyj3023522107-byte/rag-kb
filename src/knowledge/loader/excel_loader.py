from pathlib import Path
from loguru import logger

from .base import BaseLoader


class ExcelLoader(BaseLoader):
    """Excel 加载器，支持 .xlsx 和 .xls 格式"""

    def load(self) -> str:
        """加载 Excel 内容，将所有 sheet 转换为文本"""
        try:
            import pandas as pd
        except ImportError:
            raise ImportError("请安装 pandas 和 openpyxl: pip install pandas openpyxl")

        try:
            # 读取所有 sheet
            excel_file = pd.ExcelFile(self.file_path)
            all_text = []

            for sheet_name in excel_file.sheet_names:
                df = pd.read_excel(excel_file, sheet_name=sheet_name)

                if df.empty:
                    continue

                # 添加 sheet 名称作为标题
                all_text.append(f"## {sheet_name}\n")

                # 将 DataFrame 转换为文本表格
                # 去除全为 NaN 的行和列
                df = df.dropna(how='all', axis=0).dropna(how='all', axis=1)

                if df.empty:
                    continue

                # 转换为可读的文本格式
                text_parts = []

                # 获取列名
                columns = df.columns.tolist()
                if columns:
                    # 过滤掉 Unnamed 列名
                    named_cols = []
                    for i, col in enumerate(columns):
                        if isinstance(col, str) and col.startswith('Unnamed'):
                            named_cols.append(f"列{i+1}")
                        else:
                            named_cols.append(str(col))

                    # 遍历每一行
                    for idx, row in df.iterrows():
                        row_text = []
                        for col_name, value in zip(named_cols, row):
                            if pd.notna(value):
                                row_text.append(f"{col_name}: {value}")

                        if row_text:
                            text_parts.append(" | ".join(row_text))

                    if text_parts:
                        all_text.append("\n".join(text_parts))

                all_text.append("")  # sheet 之间空行

            result = "\n".join(all_text).strip()

            logger.debug(f"Excel 加载完成: {self.file_path.name}, {len(result)} 字符, {len(excel_file.sheet_names)} 个 sheet")

            return result

        except Exception as e:
            logger.error(f"Excel 加载失败: {e}")
            raise

    @classmethod
    def supports(cls, file_path: str) -> bool:
        """检查是否为 Excel 文件"""
        return Path(file_path).suffix.lower() in [".xlsx", ".xls"]

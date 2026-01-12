# author: AI
"""
Git Diff 解析器
"""

import re
import hashlib
from typing import List, Dict
from loguru import logger


class DiffParser:
    """#AI Git diff解析器"""
    
    @staticmethod
    def normalize_path(file_path: str) -> str:
        """
        #AI author: AI
        规范化文件路径，确保与前端存储的路径格式一致
        统一使用正斜杠，去除开头的斜杠或反斜杠
        
        Args:
            file_path: 原始文件路径
            
        Returns:
            规范化后的路径
        """
        if not file_path:
            return file_path
        
        # #AI 统一转换为正斜杠
        normalized = file_path.replace('\\', '/')
        
        # #AI 去除开头的斜杠或反斜杠（与前端getRelativePath保持一致）
        normalized = normalized.lstrip('/\\')
        
        return normalized
    
    @staticmethod
    def parse_diff(diff_content: str) -> Dict[str, List[str]]:
        """
        #AI 解析git diff，提取新增的代码行
        
        Args:
            diff_content: git diff输出内容
            
        Returns:
            字典，key为文件路径，value为新增的代码行列表
            {
                'file_path': ['line1', 'line2', ...],
                ...
            }
        """
        logger.info(f"[DiffParser] 开始解析 diff, 总长度: {len(diff_content)} 字符")
        
        result = {}
        current_file = None
        total_added_lines = 0
        
        lines = diff_content.split('\n')
        logger.info(f"[DiffParser] diff 包含 {len(lines)} 行")
        
        for line in lines:
            # #AI 解析文件名
            # 格式：diff --git a/src/index.ts b/src/index.ts
            if line.startswith('diff --git'):
                match = re.search(r'b/(.+)$', line)
                if match:
                    raw_file_path = match.group(1)
                    # #AI 规范化路径，确保与前端存储格式一致
                    current_file = DiffParser.normalize_path(raw_file_path)
                    result[current_file] = []
                    logger.debug(f"[DiffParser] 发现文件: {raw_file_path} -> {current_file}")
            
            # #AI 解析新增行（以+开头，但不是+++）
            elif line.startswith('+') and not line.startswith('+++'):
                if current_file:
                    # #AI 去掉开头的+号
                    code_line = line[1:]
                    result[current_file].append(code_line)
                    total_added_lines += 1
        
        logger.info(f"[DiffParser] 解析完成: {len(result)} 个文件, 共 {total_added_lines} 行新增代码")
        for file_path, file_lines in result.items():
            logger.debug(f"[DiffParser]   - {file_path}: {len(file_lines)} 行")
        
        return result
    
    @staticmethod
    def calculate_hash(content: str) -> str:
        """
        #AI 计算内容hash（与前端保持一致）
        
        Args:
            content: 代码内容
            
        Returns:
            SHA256 hash字符串
        """
        return hashlib.sha256(content.strip().encode()).hexdigest()
    
    @staticmethod
    def extract_file_changes(diff_content: str) -> Dict[str, Dict[str, int]]:
        """
        #AI 提取每个文件的变更统计
        
        Args:
            diff_content: git diff输出内容
            
        Returns:
            字典，key为文件路径，value为统计信息
            {
                'file_path': {
                    'added': 10,
                    'deleted': 5
                },
                ...
            }
        """
        result = {}
        current_file = None
        
        lines = diff_content.split('\n')
        
        for line in lines:
            # #AI 解析文件名
            if line.startswith('diff --git'):
                match = re.search(r'b/(.+)$', line)
                if match:
                    raw_file_path = match.group(1)
                    # #AI 规范化路径，确保与前端存储格式一致
                    current_file = DiffParser.normalize_path(raw_file_path)
                    result[current_file] = {'added': 0, 'deleted': 0}
            
            # #AI 统计新增行
            elif line.startswith('+') and not line.startswith('+++'):
                if current_file:
                    result[current_file]['added'] += 1
            
            # #AI 统计删除行
            elif line.startswith('-') and not line.startswith('---'):
                if current_file:
                    result[current_file]['deleted'] += 1
        
        return result


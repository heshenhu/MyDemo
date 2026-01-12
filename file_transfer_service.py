# author: AI
"""
文件传输服务
#AI author: AI
"""

import os
import shutil
import hashlib
import time
from datetime import datetime
from pathlib import Path
from sqlalchemy.orm import Session
from typing import List
from loguru import logger

from ..models import FileTransfer
from ..schemas import FileUploadRequest, FileToReceive
from ..config import get_settings


class FileTransferService:
    """#AI author: AI - 文件传输服务"""
    
    def __init__(self):
        # #AI author: AI - 从配置读取存储路径
        settings = get_settings()
        self.STORAGE_BASE = settings.FILE_STORAGE_PATH
        
        # 确保存储目录存在
        Path(self.STORAGE_BASE).mkdir(parents=True, exist_ok=True)
        logger.info(f"📁 [FileTransfer] 文件存储路径: {self.STORAGE_BASE}")
    
    def upload_file(self, db: Session, request: FileUploadRequest) -> dict:
        """
        上传文件
        
        Args:
            db: 数据库会话
            request: 上传请求
            
        Returns:
            结果字典 {file_id, server_path}
        """
        logger.info(f"========== 开始上传文件 ==========")
        logger.info(f"用户: {request.userName}")
        logger.info(f"文件: {request.fileName}")
        logger.info(f"大小: {request.fileSize} 字节")
        logger.info(f"路径: {request.filePath}")
        
        try:
            # 1. 计算文件内容hash
            content_hash = self._calculate_hash(request.content)
            logger.info(f"文件hash: {content_hash[:16]}...")
            
            # 2. 构造服务器文件路径
            user_dir = Path(self.STORAGE_BASE) / request.userName
            current_dir = user_dir / "current"
            history_dir = user_dir / "history"
            
            # 3. 确保目录存在
            current_dir.mkdir(parents=True, exist_ok=True)
            history_dir.mkdir(parents=True, exist_ok=True)
            
            # 4. 完整文件路径
            current_file_path = current_dir / request.filePath
            
            # 5. 如果文件已存在，移动到历史文件夹
            if current_file_path.exists():
                logger.info(f"文件已存在，移动到历史文件夹")
                self._move_to_history(current_file_path, history_dir, request.filePath)
            
            # 6. 确保父目录存在
            current_file_path.parent.mkdir(parents=True, exist_ok=True)
            
            # 7. 写入文件到文件系统
            current_file_path.write_text(request.content, encoding='utf-8')
            logger.info(f"文件已保存到: {current_file_path}")
            
            # 8. 记录数据库（不包含content，只保存元数据）
            file_record = FileTransfer(
                user_name=request.userName,
                file_name=request.fileName,
                file_path=request.filePath,
                status='uploaded',
                upload_time=request.timestamp,
                server_file_path=str(current_file_path),
                file_size=request.fileSize,
                language=request.language,
                file_hash=content_hash
            )
            
            db.add(file_record)
            db.commit()
            db.refresh(file_record)
            
            logger.info(f"✅ 文件上传成功: id={file_record.id}")
            logger.info(f"==============================")
            
            return {
                'file_id': file_record.id,
                'server_path': str(current_file_path)
            }
            
        except Exception as e:
            logger.error(f"❌ 文件上传失败: {e}")
            db.rollback()
            raise
    
    def _calculate_hash(self, content: str) -> str:
        """计算文件内容SHA256哈希"""
        return hashlib.sha256(content.encode('utf-8')).hexdigest()
    
    def _move_to_history(self, file_path: Path, history_dir: Path, relative_path: str):
        """
        将文件移动到历史文件夹
        
        Args:
            file_path: 当前文件路径
            history_dir: 历史文件夹路径
            relative_path: 相对路径
        """
        # 生成时间戳
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        
        # 构造历史文件名
        file_name = Path(relative_path).name
        name_parts = file_name.rsplit('.', 1)
        if len(name_parts) == 2:
            history_name = f"{name_parts[0]}_{timestamp}.{name_parts[1]}"
        else:
            history_name = f"{file_name}_{timestamp}"
        
        # 构造历史文件路径
        relative_dir = Path(relative_path).parent
        history_file_path = history_dir / relative_dir / history_name
        
        # 确保历史目录存在
        history_file_path.parent.mkdir(parents=True, exist_ok=True)
        
        # 移动文件
        shutil.move(str(file_path), str(history_file_path))
        
        logger.info(f"文件已移动到历史: {history_file_path}")
    
    def get_pending_files(self, db: Session, user_name: str) -> List[FileToReceive]:
        """
        获取待接收文件列表
        从文件系统读取内容，而不是从数据库
        
        Args:
            db: 数据库会话
            user_name: 用户名
            
        Returns:
            待接收文件列表
        """
        logger.info(f"========== 查询待接收文件 ==========")
        logger.info(f"用户: {user_name}")
        
        # 1. 查询数据库记录
        records = db.query(FileTransfer).filter(
            FileTransfer.user_name == user_name,
            FileTransfer.status == 'uploaded'
        ).order_by(FileTransfer.upload_time.desc()).all()
        
        logger.info(f"数据库中找到 {len(records)} 条记录")
        
        # 2. 从文件系统读取文件内容
        files_to_receive = []
        for record in records:
            try:
                # 从服务器文件路径读取内容
                file_path = Path(record.server_file_path)
                
                if not file_path.exists():
                    logger.error(f"文件不存在: {record.server_file_path}, id={record.id}")
                    continue
                
                # 从文件系统读取
                content = file_path.read_text(encoding='utf-8')
                
                files_to_receive.append(FileToReceive(
                    fileId=record.id,
                    fileName=record.file_name,
                    filePath=record.file_path,
                    content=content,
                    uploadTime=record.upload_time,
                    fileSize=record.file_size,
                    language=record.language
                ))
                
                logger.info(f"读取文件成功: {record.file_name}, 大小={len(content)} 字符")
                
            except Exception as e:
                logger.error(f"读取文件失败: {record.server_file_path}, error={e}")
                continue
        
        logger.info(f"✅ 成功准备 {len(files_to_receive)} 个待接收文件")
        logger.info(f"==============================")
        
        return files_to_receive
    
    def confirm_download(self, db: Session, file_id: int):
        """
        确认文件已下载
        
        Args:
            db: 数据库会话
            file_id: 文件ID
        """
        logger.info(f"========== 确认文件下载 ==========")
        logger.info(f"文件ID: {file_id}")
        
        file_record = db.query(FileTransfer).filter(FileTransfer.id == file_id).first()
        
        if not file_record:
            logger.error(f"❌ 文件记录不存在: {file_id}")
            raise ValueError(f"文件记录不存在: {file_id}")
        
        file_record.status = 'downloaded'
        file_record.download_time = int(time.time() * 1000)
        
        db.commit()
        
        logger.info(f"✅ 文件下载确认成功: {file_record.file_name}")
        logger.info(f"==============================")


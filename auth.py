# author: AI
"""
API Token 认证模块
"""

from fastapi import Header, HTTPException, status, Depends
from sqlalchemy.orm import Session
from .database import get_db
from .models import User


def verify_user_token(
    x_api_token: str = Header(None, alias="X-Api-Token"),
    x_user_name: str = Header(None, alias="X-User-Name"),
    db: Session = Depends(get_db)
) -> str:
    """
    #AI 验证用户的API Token
    
    Args:
        x_api_token: 请求头中的 X-Api-Token
        x_user_name: 请求头中的 X-User-Name
        db: 数据库会话
        
    Returns:
        验证通过的用户名
        
    Raises:
        HTTPException: Token 验证失败时抛出 401 错误
    """
    # #AI 检查必需的请求头
    if not x_user_name or not x_api_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Unauthorized"
        )
    
    # #AI 查询用户
    user = db.query(User).filter(
        User.user_name == x_user_name,
        User.is_active == True
    ).first()
    
    # #AI 用户不存在或未激活
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Unauthorized"
        )
    
    # #AI 验证 token
    if user.api_token != x_api_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Unauthorized"
        )
    
    return user.user_name


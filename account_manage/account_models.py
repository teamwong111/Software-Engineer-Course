#models.py

import sys
import jwt

sys.path.append("..")
from db_manage.sql import db

import config.config as config
from time import time
from config.config import Config

#在此处定义数据库类型对象
"""
一对一关系中，需要设置relationship中的uselist=Flase，其他数据库操作一样。
一对多关系中，外键设置在多的一方中，关系（relationship）可设置在任意一方。
多对多关系中，需建立关系表，设置 secondary=关系表
"""


class User(db.Model):
    #主键为id
    id = db.Column(db.Integer, primary_key=True)
    #不允许相同值
    username = db.Column(db.String(80), unique=True)
    #password = db.Column(db.String(80))
    hashkey = db.Column(db.String(32))
    #不允许相同值
    email = db.Column(db.String(120), unique=True)
    
    # 是否有未读消息(默认没有)
    have_unread_messages = db.Column(db.Boolean, default=False)
    #Myidentity=db.Column(db.String(80))
    
    identity = db.Column(db.String(80), unique=True)
    identity_ok = db.Column(db.Boolean)
    identity_reason = db.Column(db.String(80))
    update_identity= db.Column(db.Boolean)
    browse_list = db.Column(db.Text)#记录用户的浏览记录，不同记录之间用"_"分隔，text大小64k，存10个int绰绰有余
    collect_list = db.Column(db.Text)#用户收藏夹,不同记录之间用"_"分隔,最多添加40个收藏
    head = db.Column(db.String(80))
    is_ban = db.Column(db.Boolean)
    admin_level = db.Column(db.Integer) #管理员等级 0表示非管理员 1表示普通管理员 2表示主管理员
    def get_jwt_token(self, expires_in=600):
        """获取JWT令牌"""
        return jwt.encode(
            {
                'reset_password': self.id,
                'exp': time() + expires_in
            },
            config.Config.SECRET_KEY,
            algorithm='HS256').decode('utf8')

    @staticmethod
    def verify_jwt_token(token):
        try:
            user_id = jwt.decode(token,
                                 config.Config.SECRET_KEY,
                                 algorithms='HS256')['reset_password']
        except Exception as e:
            print(e)
            return
        return User.query.get(user_id)

    def __repr__(self):
        return '<User %r>' % self.username



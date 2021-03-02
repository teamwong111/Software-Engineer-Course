from db_manage.sql import db
import sys
from datetime import datetime

sys.path.append("..")


class Message(db.Model):
    # __tablename__ = "messages"
    id = db.Column(db.Integer, primary_key=True)                         # 消息id
    
    related_product_id =db.Column(db.Integer,nullable=False)             # 关联商品id


    sender_id = db.Column(db.Integer, nullable=False)                    # 发送者id
    sender_name = db.Column(db.String(80),nullable=False)                # 发送者昵称

    receiver_id = db.Column(db.Integer, nullable=False)                  # 接收者id
    receiver_name = db.Column(db.String(80), nullable=False)             # 接收者昵称

    already_read = db.Column(db.Boolean, default=False)                  # 消息是否已读
    message_type = db.Column(db.String(10), default="Text" )             # 消息的类型 Text:文字消息 File:文件消息
    content = db.Column(db.String(100))                                  # 文字消息的内容
    file_path = db.Column(db.String(256),default="")                     # 文件消息的文件路径
    timestamp = db.Column(db.DateTime, default=datetime.now, index=True) # 消息发送的时间戳，建立索引

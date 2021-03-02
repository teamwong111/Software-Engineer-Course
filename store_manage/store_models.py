#store_models.py
import sys


sys.path.append("..")
from db_manage.sql import db

class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80),nullable=False) #商品名称，不允许为空
    label = db.Column(db.String(20),nullable=False) #商品标签，不允许为空
    desc = db.Column(db.String(256),nullable=False) #商品描述
    price = db.Column(db.Integer,nullable=False) #商品价格
    img = db.Column(db.String(256),nullable=False) #商品图片
    uploader_name = db.Column(db.String(80),nullable=False) #上传者信息
    uploader_email = db.Column(db.String(120),nullable=False) #上传者信息
    update_admin= db.Column(db.Boolean)#是否需要审核
    identity_ok= db.Column(db.Boolean)
    identity_reason = db.Column(db.String(80))
    #uploader_contact = db.Column(db.String(120),nullable=False) #上传者信息
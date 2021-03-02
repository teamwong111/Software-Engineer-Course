# app.py

#####系统模块
from functools import wraps
from flask import Flask, request, render_template, redirect, url_for, flash, session
import os

from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import and_, or_
from flask import Flask

from flask_script import Manager
from flask_mail import Mail, Message
#####

#####自定义模块
import config.config as config
from db_manage.sql import db
from account_manage.account_models import User
from account_manage.account_views import account_app
from store_manage.store_views import store_app
from chat_manage.chat_views import chat_app
#####

app = Flask(__name__)

# 从config文件中读取配置
app.config.from_object(config.Config)

# 初始化发送邮件有关内容
manager = Manager(app)
mail = Mail(app)

# 初始化数据库对象
db.init_app(app)

@app.before_first_request
def create_db():
    # 每次启动更新一下，创建未创建过的表
    # db.drop_all()
    db.create_all()

    #虽然不知道是不是应该在这里写，但是也只能试试了
    #将根管理员信息写入数据库
    with open('config/admin', 'r', encoding='utf-8') as f:
        content = f.read().splitlines()
    l = len(content)
    for index in range(0, l, 2):
        if not User.query.filter(and_(User.username == content[index], User.hashkey == content[index+1])).first():
            user = User(username=content[index],
                        hashkey=content[index+1],
                        email="lby1570975210@gmail.com",
                        identity_ok=True,
                        update_identity=False,
                        head='../static/head_images/start.jpg',
                        is_ban=False,
                        admin_level=2)
            db.session.add(user)
            db.session.commit()



# 注册蓝图
# 账号信息
# 商品信息
# 聊天信息
app.register_blueprint(account_app)
app.register_blueprint(store_app)
app.register_blueprint(chat_app)
if __name__ == '__main__':
    app.run(debug=True)

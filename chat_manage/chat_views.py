# chat_views.py
# 账户视图模块
# 系统导入
from account_manage.account_views import login_required
from store_manage.store_models import Product
from account_manage.account_models import User
from chat_manage.chat_models import Message
from db_manage.sql import db
from functools import wraps
from sqlalchemy import and_, or_
from flask import request, render_template, redirect, url_for, flash, session, Blueprint, jsonify
from werkzeug.utils import secure_filename
import os
# import cv2
import time
import sys
import datetime
import random
import uuid

from selenium import webdriver

#
sys.path.append("..")

# 跨文件路由需要蓝图
chat_app = Blueprint('chat', __name__)

# 显示消息列表
@chat_app.route("/message_list")
@login_required
def message_list():
    username = session.get('username')
    user = User.query.filter(User.username == username).first()

    pord_list = Product.query.all()
    class chatwith_info(object):
        def __init__(self, prod, userid, username,have_unread_message=0):
            self.prod=prod
            self.userid=userid
            self.username=username
            self.have_unread_message=have_unread_message
    all_chatwith_list=[]
    for prod in pord_list:
        msg_list1=Message.query.filter_by(related_product_id=prod.id,sender_id=user.id).all()
        msg_list2=Message.query.filter_by(related_product_id=prod.id,receiver_id=user.id).all()
        msg_list=msg_list1+msg_list2
        chatwith_list=[]
        id_list=[]
        if msg_list:
            for msg in msg_list:
                if msg.sender_id !=user.id and (msg.sender_id not in id_list):
                    chatwith_list.append(chatwith_info(prod,msg.sender_id,msg.sender_name))
                    id_list.append(msg.sender_id)
                if msg.receiver_id !=user.id and (msg.receiver_id not in id_list):
                    chatwith_list.append(chatwith_info(prod,msg.receiver_id,msg.receiver_name))
                    id_list.append(msg.receiver_id)
            all_chatwith_list.append(chatwith_list)

    for list in all_chatwith_list:
        for info in list:
            msg_list=Message.query.filter_by(related_product_id=info.prod.id,sender_id= info.userid,receiver_id=user.id,already_read=False).all()
            if msg_list:
                info.have_unread_message=1


   
    return render_template('message_list.html',  all_chatwith_list=all_chatwith_list, user_id=user.id, username=session.get('username'))

# 取得时间戳的关键字
def get_timestamp_key(elem):
    return elem.timestamp


# 获取消息记录 msg_show_num：要获取的消息条数，默认10 ， before_location:从消息列表末尾的第x条消息开始获取，默认为0
def get_msg_list(product_id, user_1_id, user_2_id, msg_show_num=10,before_location=0):
    list1=Message.query.filter_by(
        related_product_id=product_id,sender_id= user_1_id, receiver_id=user_2_id).all()
    list2=Message.query.filter_by(
        related_product_id=product_id,sender_id= user_2_id, receiver_id=user_1_id).all()
    msg_list=list1+list2
    msg_list.sort(key=get_timestamp_key, reverse=False)
    msg_num=len(msg_list)
    if msg_show_num<=0: # 展示数量小于0直接返回所有消息
        return msg_list
    if before_location <= 0: #从最后一条消息获取
        if  msg_num > msg_show_num:
            msg_list= msg_list[-msg_show_num:]
    elif before_location > 0 and before_location < msg_num: #从跳过x条消息之后开始获取
        if  msg_num > msg_show_num :
            if msg_show_num+before_location <= msg_num:
                msg_list= msg_list[-msg_show_num-before_location:msg_num-before_location-1]
            else:
                msg_list= msg_list[0:msg_num-before_location-1]
        else:
                msg_list= msg_list[0:msg_num-before_location-1]
    else:
        if msg_num > msg_show_num:
            msg_list=msg_list[0:msg_show_num-1]

    return msg_list

# 聊天交互界面
@chat_app.route('/chat/<int:user_id>/<int:chat_partner_id>/<int:product_id>', methods=['GET', 'POST'])
@login_required
def chat(user_id, chat_partner_id,product_id):
    if user_id == chat_partner_id:
        flash(u'不能与自己聊天！', 'danger')
        return redirect(url_for('user.home'))

    user = User.query.filter(User.username==session.get('username')).first()
    
    if user.id != user_id:
        flash(u'不能使用他人的账号聊天！', 'danger')
        return redirect(url_for('user.home'))

    chat_partner = User.query.filter_by(id=chat_partner_id).first()

    product = Product.query.filter(Product.id == product_id).first()
    if product.uploader_name != user.username and product.uploader_name != chat_partner.username:
        flash(u'这件商品不属于你们！', 'danger')
        return redirect(url_for('user.home'))

    chat_partner.have_unread_message = True
    db.session.commit()
    if request.method == 'POST':
        # 接受表单提交的消息存入数据库
        msg=Message(
            related_product_id=product_id,
            sender_id=user_id,
            sender_name=user.username,
            receiver_id=chat_partner_id,
            receiver_name=chat_partner.username,
            content=request.form["Text"]
            )
        db.session.add(msg)
        db.session.commit()

    # 更改未读消息的状态
    unread_list = Message.query.filter_by(
        related_product_id=product_id,sender_id=chat_partner_id, receiver_id=user_id,already_read=False).all()
    for msg in unread_list:
        msg.already_read=True
    db.session.commit()


    # 检查是否有未读消息
    # all_unread_list = Message.query.filter_by(receiver_id=user.id, already_read=False).all()
    # if len(all_unread_list) == 0:
    #     user.have_unread_messages = False
    # else:
    #     user.have_unread_messages = True
    # db.session.commit()

    # 获取10条历史消息
    message_list=get_msg_list(product_id,user_id,chat_partner_id,10)
    

    #测试用
    # class message(object):
    #     def __init__(self, sender_name,content):
    #         self.sender_name=sender_name
    #         self.content=content
    #
    # msg_1=message("p1","hello") 
    # msg_2=message("p2","hi!")
    # message_list=[msg_1,msg_2]

    return render_template('chat.html', message_list=message_list,user_id=user_id,chat_partner_id=chat_partner_id,product_id=product_id,user=session.get('user'),username=session.get('username'),chat_partner_name=chat_partner.username)


@chat_app.route('/chat_records/<int:user_id>/<int:chat_partner_id>/<int:product_id>/<location>', methods=['GET', 'POST'])
@login_required
def chat_records(user_id, chat_partner_id, product_id, location):
    
    user = User.query.filter(
        User.username == session.get('username')).first()
    
    if user.id != user_id:
        flash(u'不能访问他人的聊天记录！', 'danger')
        return redirect(url_for('chat.message_list'))

    all_message_list = get_msg_list(product_id, user_id, chat_partner_id, 0)
    msg_num = len( all_message_list)
    location=int(location)
    if location >= msg_num:
        flash(u'没有更多历史消息！', 'danger')
        location = location-10
    elif location < 0:
        flash(u'已经是最新的消息！', 'danger')
        location = location +10
    message_list = get_msg_list(product_id, user_id, chat_partner_id,10, location)

    return render_template('chat_records.html',message_list=message_list,user_id=user_id,chat_partner_id=chat_partner_id,product_id=product_id,location=location,username=session.get('username'))


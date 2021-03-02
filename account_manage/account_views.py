# account_views.py
# 账户视图模块
# 系统导入
from account_manage import email
from store_manage.store_models import Product
from account_manage.account_models import User
from chat_manage.chat_models import Message
from db_manage.sql import db
from functools import wraps
from sqlalchemy import and_, or_
from flask import request, render_template, redirect, url_for, flash, session, Blueprint, jsonify, make_response, current_app
from flask_mail import Mail
from werkzeug.utils import secure_filename
import os
#import cv2
import time
import sys
import datetime
import random
import re
import hashlib
import flask_paginate

from datetime import timedelta
import uuid

from selenium import webdriver
#
sys.path.append("..")
#from form import ResetPasswordRequestForm

# 跨文件路由需要蓝图
account_app = Blueprint('user', __name__)

# 辅助函数


# 登录检验（用户名、密码验证）
def valid_login(username, hashkey):
    user = User.query.filter(
        and_(User.username == username, User.hashkey == hashkey)).first()
    if user:
        if user.is_ban == False:
            return 1
        else:
            return 2
    else:
        return 3


# 注册检验（用户名、邮箱验证）
def valid_regist(username, email):
    user = User.query.filter(
        or_(User.username == username, User.email == email)).first()
    if user:
        return False
    else:
        return True

# 重置密码检验（用户名、邮箱验证）


def valid_reset(username, email):
    user = User.query.filter(
        and_(User.username == username, User.email == email)).first()
    if user:
        return False
    else:
        return True


# 登录
def login_required(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        # if g.user:
        if session.get('username'):
            return func(*args, **kwargs)
        else:
            return redirect(url_for('user.login', next=request.url))  #

    return wrapper


# 路由


# 0. 返回ico图标
@account_app.route('/favicon.ico')
def favicon():
    # 后端返回文件给前端（浏览器），send_static_file是Flask框架自带的函数
    return current_app.send_static_file('img/favicon.png')


# 1.主页
@account_app.route('/')
def home():

    product = Product.query.filter_by(identity_ok=True).all()  # 从服务器取得数据
    list = []
    length = len(product)
    per_page = 12  # 每页显示十二个商品
    page = int(request.args.get('page', 1))  # 获取页码
    paginate = Product.query.filter_by(identity_ok=True).paginate(
        page, per_page, error_out=False)  # 创建分页器对象
    page_product = paginate.items
    if length > 5:
        for i in range(0, 5, 1):

            while 1:
                r = random.randint(0, length - 1)
                if product[r] in list:
                    continue
                else:
                    break
            list.append(product[r])
    else:
        list = product

    return render_template('home.html',
                           username=session.get('username'),
                           product=product,
                           list=list,
                           page_product=page_product,
                           paginate=paginate)


# 2.登录
'''
@account_app.route('/login', methods=['GET', 'POST'])
def login():

    if request.method == 'POST':
        Username = request.form['username']
        Password = request.form['password']
        with open('config/administrator0.txt', 'r') as f:
            content = f.read().splitlines()
        l = len(content)
        flag = False
        for index in range(0, l, 2):
            if content[index] == Username and content[index+1] == Password:
                flag = True
        if flag:
            return redirect(url_for('user.admin', getname='0'))
        with open('config/administrator1.txt', 'r') as f:
            content = f.read().splitlines()
        l = len(content)
        flag = False
        for index in range(0, l, 2):
            if content[index] == Username and content[index+1] == Password:
                flag = True
        if flag:
            return redirect(url_for('store.admin_picture', getname='0'))
        with open('config/administrator2.txt', 'r') as f:
            content = f.read().splitlines()
        l = len(content)
        flag = False
        for index in range(0, l, 2):
            if content[index] == Username and content[index+1] == Password:
                flag = True
        if flag:
            return redirect(url_for('user.admin_account', getname='0'))
        if valid_login(request.form['username'], request.form['password'])==1:
            flash("成功登录！",'success')
            session['username'] = request.form.get('username')
            return redirect(url_for('user.home'))
        else:
            if valid_login(request.form['username'], request.form['password'])==3:
                flash(u'错误的用户名或密码！','danger')
            else:
                flash(u'账号被封禁，请联系管理员！','danger')

    return render_template('login.html')
'''

# 2.登录
@account_app.route('/login', methods=['GET', 'POST'])
def login():

    if request.method == 'POST':
        Username = request.form['username']
        Password = request.form['password']
        hash = hashlib.sha256()
        hash.update('buybuy'.encode('utf-8'))
        hash.update(Password.encode('utf-8'))
        hashkey = hash.hexdigest()
        if valid_login(request.form['username'], hashkey) == 1:
            flash(u"成功登录！", 'success')
            session['username'] = request.form.get('username')
            user = User.query.filter(
                User.username == request.form.get('username')).first()
            if user and user.admin_level:
                return redirect(url_for('user.panel'))
            return redirect(url_for('user.home'))
        else:
            if valid_login(request.form['username'], hashkey) == 3:
                flash(u'错误的用户名或密码！', 'danger')
            else:
                flash(u'账号被封禁，请联系管理员！', 'danger')

    return render_template('login.html')

# 3.注销
@account_app.route('/logout')
def logout():
    session.pop('username', None)
    flash(u"已注销", 'success')
    return redirect(url_for('user.home'))


# 4.注册
@account_app.route('/regist', methods=['GET', 'POST'])
def regist():

    if request.method == 'POST':
        if len(request.form['username']) == 0 or len(request.form['username']) > 30:
            flash(u'用户名长度必须在1-30个字符内', 'danger')
            return render_template('regist.html')
        if len(request.form['password1']) < 6 or len(request.form['password1']) > 30:
            flash(u'密码长度必须在6-30个字符内', 'danger')
            return render_template('regist.html')
        E_mail = request.form['email']
        if re.match(r'^[0-9a-zA-Z_]{0,19}@[0-9a-zA-Z]{1,13}(\.edu)?\.[com,cn,net]{1,3}$', E_mail):
            E_mail = E_mail
        else:
            flash(u'邮箱格式不正确', 'danger')
            return render_template('regist.html')
        if request.form['password1'] != request.form['password2']:
            flash(u'两次密码不相同！', 'danger')
        elif valid_regist(request.form['username'], request.form['email']):
            hash = hashlib.sha256()
            hash.update('buybuy'.encode('utf-8'))  # salt
            hash.update(request.form['password1'].encode('utf-8'))
            user = User(username=request.form['username'],
                        hashkey=hash.hexdigest(),
                        email=request.form['email'],
                        identity_ok=False,
                        update_identity=False,
                        head='../static/head_images/start.jpg',
                        is_ban=False,
                        admin_level=0)
            db.session.add(user)
            db.session.commit()

            flash(u"注册成功！", 'success')
            return redirect(url_for('user.login'))
        else:
            flash(u'该用户名或邮箱已被注册！', 'danger')

    return render_template('regist.html')


# 5.个人中心
@account_app.route('/panel')
@login_required
def panel():
    username = session.get('username')
    user = User.query.filter(User.username == username).first()
    # 检查是否有未读消息
    all_unread_list = Message.query.filter_by(
        receiver_id=user.id, already_read=False).all()
    if len(all_unread_list) == 0:
        user.have_unread_messages = False
    else:
        user.have_unread_messages = True
        flash(u'您有新的未读消息！', 'info')
    db.session.commit()
    return render_template("panel.html",
                           user=user,
                           username=session.get('username'))


# 6.修改密码


@account_app.route('/change', methods=['GET', 'POST'])
@login_required
def change():
    if request.method == 'POST':
        hash = hashlib.sha256()
        hash.update('buybuy'.encode('utf-8'))
        hash0 = hashlib.sha256()
        hash0.update('buybuy'.encode('utf-8'))
        hash0.update(request.form['password0'].encode('utf-8'))
        if len(request.form['password1']) < 6 or len(request.form['password1']) > 30:
            flash(u'密码长度必须在6-30个字符内', 'warning')
            return render_template('change.html', username=session.get('username'))
        username = session.get('username')
        user = User.query.filter(User.username == username).first()
        if user.hashkey == hash0.hexdigest():
            if request.form['password1'] == request.form['password2']:
                hash.update(request.form['password1'].encode('utf-8'))
                user.hashkey = hash.hexdigest()
                db.session.commit()
                flash(u"密码修改成功", 'success')
                return redirect(url_for('user.login'))
            else:
                flash(u'两次密码输入不相同！', 'warning')
        else:
            flash(u'原密码错误', 'warning')
    return render_template('change.html',
                           username=session.get('username'))


# 7.忘记密码
@account_app.route('/reset', methods=['GET', 'POST'])
def reset():
    if request.method == 'POST':
        useremail = request.form['email']

        if valid_reset(request.form['name'], request.form['email']):
            flash(u'用户名或邮箱输入错误！', 'warning')
        else:
            # error='用户名或邮箱存在'
            user = User.query.filter(User.email == useremail).first()
            email.send_password_reset_email(user)
            flash(u'成功发送验证邮件！', 'success')
    return render_template('reset.html', username=session.get('username'))


# 重置密码（也属于忘记密码当中的）
@account_app.route('/reset_/<token>', methods=['GET', 'POST'])
def reset_1(token):

    #token = request.form['token']
    if request.method == 'POST':
        user = User.verify_jwt_token(token)
        if not user:
            flash(u'这是管理员账号！', 'warning')
            print("串：", token)
            #driver = webdriver.Chrome()
            #currentPageUrl = driver.current_url
            #print("当前页面的url是：", currentPageUrl)
            return redirect(url_for('user.regist'))
        else:
            if len(request.form['password1']) < 6 or len(request.form['password1']) > 30:
                flash(u'密码长度必须在6-30个字符内', 'warning')
                return render_template('reset_.html', username=session.get('username'))
            if request.form['password1'] == request.form['password2']:
                hash = hashlib.sha256()
                hash.update('buybuy'.encode('utf-8'))
                hash.update(request.form['password1'].encode('utf-8'))
                user.hashkey = hash.hexdigest()
                db.session.commit()
                # db.session.delete(user)
                # db.session.commit()
                # db.session.add(u)
                # db.session.commit()
                flash("密码修改成功", 'success')
                return redirect(url_for('user.login'))
            else:
                flash(u'两次输入密码不相同!', 'warning')
    return render_template('reset_.html', username=session.get('username'))


# 8.身份认证

# 设置允许的文件格式
ALLOWED_EXTENSIONS = set(['png', 'jpg', 'JPG', 'PNG', 'bmp'])


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS


# 设置静态文件缓存过期时间
account_app.send_file_max_age_default = timedelta(seconds=1)


# 用户上传图片
@account_app.route('/identity', methods=['POST', 'GET'])
@login_required
def identity():
    username = session.get('username')
    if request.method == 'POST':

        user = User.query.filter(User.username == username).first()
        f = request.files['file']
        if not (f and allowed_file(f.filename)):
            flash(u"请检查上传的图片类型，仅限于png、jpg、bmp", 'warning')
        else:
            basepath = os.path.dirname(__file__)

            # basepath = os.path.abspath(os.path.join(os.path.dirname("__file__"),os.path.pardir))#基目录为上一级目录
            # fname = secure_filename(f.filename)
            ext = os.path.splitext(f.filename)[1]
            new_filename = str(uuid.uuid1()) + ext
            # 注意：没有的文件夹一定要先创建，不然会提示没有该路径
            upload_path = os.path.join(basepath, '../static/identity_images',
                                       new_filename)
            f.save(upload_path)  # 这个dubug过，可以成功保存
            if user.identity:  # 删除原来的图片
                del_path = os.path.join(basepath, '../static/', user.identity)
                if os.path.exists(del_path):
                    os.remove(del_path)
            user.identity = 'identity_images/' + new_filename
            user.update_identity = True
            db.session.commit()
            flash(u'上传成功！', 'success')
            return redirect(url_for('user.panel'))
            # return render_template('panel.html', user=user, username=username)
    return render_template('identity.html', username=username)


# 审核用户

@account_app.route('/admin/examine', methods=['POST', 'GET'])
@account_app.route('/admin/examine/<getname>', methods=['POST', 'GET'])
@login_required
def admin_examine(getname=""):
    cur_user = User.query.filter(
        User.username == session.get('username')).first()
    if not (cur_user and cur_user.admin_level):
        flash(u'请使用管理员账号登录！', 'danger')
        return redirect(url_for('user.login'))

    if request.method == 'POST':
        user = User.query.filter(User.username == getname).first()
        if user:
            if request.form.get('pass') == 'no':
                user.identity_ok = False
                user.identity_reason = request.form.get('reason1')
            elif request.form.get('pass') == 'yes':
                user.identity_ok = True
            user.update_identity = False
            db.session.commit()
        return redirect(url_for('user.admin_examine'))

    users_get = User.query.all()
    users = []
    for uu in users_get:
        if uu.update_identity:  # 寻找所有的更新过信息的用户
            users.append(uu)
    # if request.form.get('back') == '1':
    #    return redirect(url_for('user.home'))
    return render_template('admin_examine.html', users=users)

# 9 修改昵称


@account_app.route('/changeName', methods=['GET', 'POST'])
@login_required
def changeName():

    if request.method == 'POST':
        username = request.form['username']
        user = User.query.filter(User.username == username).first()
        if user:
            flash(u'用户名已存在', 'warning')
            return render_template('changeName.html', username=session.get('username'))
        if len(request.form['username']) == 0 or len(request.form['username']) > 30:
            flash(u'用户名长度必须在1-30个字符内', 'warning')
            return render_template('changeName.html', username=session.get('username'))
        username = session.get('username')
        user = User.query.filter(User.username == username).first()
        user.username = request.form['username']
        db.session.commit()
        flash("昵称修改成功", 'success')
        session['username'] = user.username
        return redirect(url_for('user.panel'))
        # return render_template('panel.html', user=user, username=user.username)
    return render_template('changeName.html',
                           username=session.get('username'))


# 10.  修改头像

@account_app.route('/changeHead', methods=['POST', 'GET'])
@login_required
def changeHead():
    username = session.get('username')
    if request.method == 'POST':

        user = User.query.filter(User.username == username).first()
        f = request.files['file']
        if not (f and allowed_file(f.filename)):
            flash(u"请检查上传的图片类型，仅限于png、PNG、jpg、JPG、bmp", 'warning')
        else:
            basepath = os.path.dirname(__file__)

            # basepath = os.path.abspath(os.path.join(os.path.dirname("__file__"),os.path.pardir))#基目录为上一级目录
            # fname = secure_filename(f.filename)
            ext = os.path.splitext(f.filename)[1]
            new_filename = str(uuid.uuid1()) + ext
            # 注意：没有的文件夹一定要先创建，不然会提示没有该路径
            upload_path = os.path.join(basepath, '../static/head_images',
                                       new_filename)
            f.save(upload_path)  # 这个dubug过，可以成功保存
            if user.head and user.head != '../static/head_images/start.jpg':  # 删除原来的图片
                del_path = os.path.join(basepath, '../static/', user.head)
                if os.path.exists(del_path):
                    os.remove(del_path)
            user.head = 'head_images/' + new_filename
            db.session.commit()
            return redirect(url_for('user.panel'))
            # return render_template('panel.html', user=user,username=username)
    return render_template('changeHead.html', username=username)


@account_app.route('/admin/account', methods=['POST', 'GET'])
@login_required
def admin_account():
    cur_user = User.query.filter(
        User.username == session.get('username')).first()
    if not (cur_user and cur_user.admin_level):
        flash(u'请使用管理员账号登录！', 'danger')
        return redirect(url_for('user.login'))

    if request.method == 'POST':
        Username = request.form['username']
        user = User.query.filter(User.username == Username).first()
        if user:
            if user.admin_level >= cur_user.admin_level:
                flash(u'无权封禁或解封该账号！请联系主管理员', 'danger')
            if request.form.get('is_pass') == 'no':
                if user.is_ban == False:
                    flash(u'该账号未被封禁', 'danger')
                else:
                    flash('解封成功', 'success')
                    user.is_ban = False
                    db.session.commit()
            elif request.form.get('is_pass') == 'yes':
                if user.is_ban == True:
                    flash(u'该账号已被封禁', 'danger')
                else:
                    flash('封号成功', 'success')
                    user.is_ban = True
                    db.session.commit()
        else:
            flash(u'该账号不存在', 'danger')
        #return redirect(url_for('user.admin_account'))
    return render_template('admin_account.html')

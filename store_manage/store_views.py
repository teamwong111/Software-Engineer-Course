# account_views.py
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
store_app = Blueprint('store', __name__)

# 辅助函数

# 1.添加商品信息

# 设置允许的文件格式
# ALLOWED_EXTENSIONS = set(['png', 'jpg', 'JPG', 'PNG', 'bmp', 'BMP', 'jpeg', 'JPEG', 'gif', 'GIF'])
ALLOWED_EXTENSIONS = set(['png', 'jpg', 'jpeg', 'gif', 'bmp'])


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS


# def create_uuid():  # 生成唯一的图片的名称字符串，防止图片显示时的重名问题
#     nowTime = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
#     # 生成当前时间
#     randomNum = random.randint(0, 100)
#     # 生成的随机整数n，其中0<=n<=100
#     if randomNum <= 10:
#         randomNum = str(0) + str(randomNum)
#     uniqueNum = str(nowTime) + str(randomNum)
#     return uniqueNum


@store_app.route('/productAdd', methods=['GET', 'POST'])
@login_required
def productAdd():
    username = session.get('username')
    if not username:
        flash(u"请先登录！", "danger")
        return redirect(url_for("user.home"))

    user = User.query.filter(User.username == username).first()

    if not user.identity_ok:
        flash(u"未通过身份认证，请先进行认证！", "danger")
        return redirect(url_for("user.panel"))

    if request.method == 'POST':
        f = request.files.get('img')
        if not f:
            flash(u"未上传图片！", 'warning')
            return render_template('productAdd.html', username=username)
        f.filename = f.filename.lower()

        if not (f and allowed_file(f.filename)):
            flash(u"请检查上传的图片类型，仅限于png, jpg, jpeg, gif, bmp", "warning")
            return redirect(url_for('store.productAdd'))
            # return jsonify({
            #     "error": 1001,
            #     "msg": "请检查上传的图片类型，仅限于png、PNG、jpg、JPG、bmp"
            # })

        basepath = os.path.dirname(__file__)
        # basepath = os.path.abspath(os.path.join(os.path.dirname("__file__"),os.path.pardir))#基目录为上一级目录
        # fname = secure_filename(f.filename)
        ext = os.path.splitext(f.filename)[1]
        new_filename = str(uuid.uuid1()) + ext
        # 注意：没有的文件夹一定要先创建，不然会提示没有该路径
        upload_path = os.path.join(basepath, '../static/store_images',
                                   new_filename)
        f.save(upload_path)  # 这个debug过，可以成功保存
        if not (user.identity_ok):
            flash(u"未进行身份认证，请先完成认证！", "error")
            return redirect(url_for('user.panel'))
        product = Product(
            name=request.form.get('name'),
            desc=request.form.get('desc'),
            label=request.form.get('label'),
            price=request.form.get('price'),
            # price = session.get('price'),#测bug用的
            # uploader_contact = request.form['contact'],#之前数据库里没有这个，就不加了吧
            #   img=os.path.join('store_images/', new_filename),
            img='store_images/' + new_filename,
            uploader_name=user.username,
            uploader_email=user.email,  # 我在想要不要有qq之类的联系方式
            update_admin=True,
            identity_ok=False
        )

        # print(upload_path)

        db.session.add(product)
        db.session.commit()
        flash(u"商品添加成功！", "success")
        return redirect(url_for('store.my_prod'))
    return render_template('productAdd.html', username=username)


#   2.搜索商品
'''def comp_item_keyword(keyword_list):
    item_found=Product.Query.filter(Product.name.in_(keyword_list)).all()
    return item_found             #返回符合关键字的商品的列表'''


@store_app.route('/getsearch', methods=['GET', 'POST'])
@store_app.route('/getsearch/<path:key_word>', methods=['GET', 'POST'])
@login_required
def get_item(key_word=''):
    if request.method == 'POST':
        keyword = request.form.get('keyword')
        keyword_list = keyword.split()  # 把整个字符串按照空格分成各个列表，分割关键字
        # 利用set去重
        prod_found = set()
        for keyword_name in keyword_list:
            prod_this_keyword = Product.query.filter(
                and_(Product.name.like("%" + keyword_name + "%"), Product.identity_ok)).all()
            for prod in prod_this_keyword:
                prod_found.add(prod)
        return render_template('SearchResult.html',
                               keyword=keyword,
                               username=session.get('username'),
                               item_list=list(prod_found))
    else:
        keyword_list = key_word.split()  # 把整个字符串按照空格分成各个列表，分割关键字
        # 利用set去重
        prod_found = set()
        for keyword_name in keyword_list:
            prod_this_keyword = Product.query.filter(
                and_(Product.name.like("%" + keyword_name + "%"), Product.identity_ok)).all()
            for prod in prod_this_keyword:
                prod_found.add(prod)
        return render_template('SearchResult.html',
                               keyword=key_word,
                               username=session.get('username'),
                               item_list=list(prod_found))


#   3.显示商品详情页
@store_app.route('/show_item', methods=['GET', 'POST'])
@store_app.route('/show_item/<key_word>/<item_id>', methods=['GET', 'POST'])
@login_required
def show_item(key_word, item_id):
    item = Product.query.filter_by(id=item_id).first()  # 取得要查看的商品

    # 将商品id添加到browse_list中
    username = session.get('username')
    user = User.query.filter(User.username == username).first()

    # 判断商品是否在收藏夹里
    isCollect = 0
    if user.collect_list is not None:
        item_collect_list = user.collect_list.split("_")
        if str(item.id) in item_collect_list:
            isCollect = 1

    if user.browse_list is None:
        user.browse_list = str(item_id)

    else:
        item_browse_list = user.browse_list.split("_")
        if str(item_id) in item_browse_list:
            # 如果之前存在，那么将其删除再更新到尾巴
            item_browse_list.remove(str(item_id))
            item_browse_list.append(str(item_id))
        else:  # 如果之前不存在，那么判断已浏览的个数
            if len(item_browse_list) >= 10:
                item_browse_list.pop(0)
            item_browse_list.append(str(item_id))

        user.browse_list = ""
        for item_browse in item_browse_list:
            user.browse_list = user.browse_list + "_" + item_browse

    db.session.commit()
    seller = User.query.filter(User.username == item.uploader_name).first()
    return render_template('show_item.html', key_word=key_word, item=item, username=session.get('username'),
                           isCollect=isCollect, user_id=user.id, seller_id=seller.id, product_id=item.id)


#  4.查看商品列表

@store_app.route('/myprod', methods=['GET', 'POST'])
@login_required
def my_prod():
    username = session.get('username')
    user = User.query.filter(User.username == username).first()
    prod_list = Product.query.filter(
        Product.uploader_name == user.username).all()  # 寻找所有创建者为本人的商品
    return render_template('my_prod.html', prod_list=prod_list, username=user.username)


#  5.删除商品


@store_app.route('/delprod', methods=['GET', 'POST'])
@login_required
def del_prod():
    prod_del_id = request.args.get('prod_del_id')
    prod_del = Product.query.filter_by(id=prod_del_id).first()

    if prod_del.uploader_name != session.get('username'):
        flash(u"不是本人的商品", 'danger')
        return redirect(url_for('store.my_prod'))

    base_path = os.path.dirname(os.path.dirname(__file__))
    abs_path = os.path.join(base_path, 'static/store_images',
                            os.path.basename(
                                prod_del.img))  # 获取要删除的本地图片的绝对路径
    # 删除数据库中的对象
    db.session.delete(prod_del)
    db.session.commit()
    # 删除本地保存的图片
    if os.path.exists(abs_path):
        os.remove(abs_path)
    # 删除相关商品的所有聊天记录
    msg_del_list=Message.query.filter_by(related_product_id=prod_del_id).all()
    for msg in msg_del_list:
        db.session.delete(msg)
    db.session.commit()

    return redirect(url_for('store.my_prod'))


#  6.修改商品信息


@store_app.route('/modifyprod/<prod_id>', methods=['GET', 'POST'])
@login_required
def modify_prod(prod_id):
    prod_modify = Product.query.filter_by(id=prod_id).first()
    if not prod_modify:
        flash(u"不存在的商品", 'warning')
        return redirect(url_for('store.my_prod'))
    if prod_modify.uploader_name != session.get('username'):
        flash(u"不是本人的商品", 'danger')
        return redirect(url_for('store.my_prod'))
    if request.method == 'POST':
        base_path = os.path.dirname(os.path.dirname(__file__))
        abs_path = os.path.join(base_path, 'static/store_images',
                                os.path.basename(
                                    prod_modify.img))  # 获取要删除的本地图片的绝对路径
        f = request.files.get('img')

        if f:
            if not allowed_file(f.filename):
                error = "请检查上传的图片类型，仅限于png, jpg, jpeg, gif, bmp"
                return render_template('modify_prod.html', username=session.get('username'), prod=prod_modify)
            else:
                basepath = os.path.dirname(__file__)
                ext = os.path.splitext(f.filename)[1]
                new_filename = str(uuid.uuid1()) + ext
                upload_path = os.path.join(basepath, '../static/store_images',
                                           new_filename)
                f.save(upload_path)
                prod_modify.img = 'store_images/' + new_filename
                if os.path.exists(abs_path):
                    os.remove(abs_path)

        prod_modify.name = request.form.get('name')
        prod_modify.desc = request.form.get('desc')
        prod_modify.label = request.form.get('label')
        prod_modify.price = request.form.get('price')
        prod_modify.update_admin = True
        prod_modify.identity_ok = False
        db.session.commit()
        flash(u"商品修改成功，请等待重新审核", 'success')
        return redirect(url_for('store.my_prod'))

    return render_template('modify_prod.html', username=session.get('username'), prod=prod_modify)


'''@store_app.route('/admin_picture', methods=['POST', 'GET'])
# @account_app.route('/admin', methods=['POST', 'GET'])
def admin_picture():
    prods_get = Product.query.all()
    prods = []
    for uu in prods_get:
        if uu.update_admin:  #寻找所有的更新过信息的用户
            prods.append(uu)
    return render_template('admin_picture.html', products=prods)
@store_app.route('/all_pass',methods=['POST'])
def all_pass():
    pass_ids=request.values.getlist("pass1")
    for pass_id in pass_ids:
        pass_one=Product.query.filter(Product.name == pass_id).first()
        pass_a=Product(id=pass_one.id,
                       name=pass_one.name,
                       label=pass_one.label,
                       desc=pass_one.desc,
                       price=pass_one.price,
                       img=pass_one.img,
                       uploader_name=pass_one.uploader_name,
                       uploader_email=pass_one.uploader_email,
                       update_admin=False,
                       identity_ok=True,
                       identity_reason=""
                       )
        db.session.delete(pass_one)
        db.session.commit()
        db.session.add(pass_a)
        db.session.commit()'''
        
@store_app.route('/admin/picture', methods=['POST', 'GET'])
@store_app.route('/admin/picture/<getname>', methods=['POST', 'GET'])
@login_required
def admin_picture(getname=""):

    cur_user = User.query.filter(
        User.username == session.get('username')).first()
    if not (cur_user and cur_user.admin_level):
        flash(u'请使用管理员账号登录！', 'danger')
        return redirect(url_for('user.login'))
    
    if request.method == 'POST':
        prod = Product.query.filter(Product.id == getname).first()
        if prod:
            if request.form.get('pass') == 'no':
                prod.identity_ok = False
                prod.identity_reason = request.form.get('reason1')
            elif request.form.get('pass') == 'yes':
                prod.identity_ok = True
            prod.update_admin = False
            db.session.commit()
        return redirect(url_for('store.admin_picture'))
            
    prods_get = Product.query.all()
    prods = []
    for uu in prods_get:
        if uu.update_admin:  # 寻找所有的更新过信息的用户
            prods.append(uu)
    return render_template('admin_picture.html', products=prods, username=session.get('username'))


#  7.查看浏览记录
@store_app.route('/mybrowse', methods=['GET', 'POST'])
@login_required
def my_browse():
    username = session.get('username')
    user = User.query.filter(User.username == username).first()
    # prod_list = Product.query.filter(
    #     Product.uploader_name == user.username).all()  # 寻找所有创建者为本人的商品

    prod_list = []  # 如果浏览记录为空，则返回空列表
    if user.browse_list is not None:  # 如果浏览记录不为空，添加列表内容
        browse_list = user.browse_list.split('_')

        while '' in browse_list:
            browse_list.remove('')
        # ps：我在测试的时候，list里面出现了空元素''，debug之后，现在改正了，不会出现空元素
        # 加入这句话为了以防万一
        for item_id in browse_list:
            item_obj = Product.query.filter(and_(Product.id == int(item_id), Product.identity_ok)).first()
            if item_obj is not None:
                prod_list.append(item_obj)
        prod_list.reverse()  # 最近浏览的商品，放在最前面
    return render_template('my_browse.html', prod_list=prod_list, username=user.username)


#   8.删除浏览记录
#   在查看浏览记录的网页my_browse.html中添加了一个超链接，该链接指向/edit_my_browse
#   初次点击链接会调用函数并跳转到新的网页del_my_browse.html，这个网页只有[删除浏览记录]的作用
#   该网页用表单form提交信息给后台，用input的checkbox属性组成复选框，选择要删除的浏览记录
#   提交表单时，表单用post方法提交到edit_my_browse
#   要求form中属性为checkbox的input 的name是sel_prod

@store_app.route('/edit_my_browse', methods=['GET', 'POST'])
@login_required
def del_my_browse():
    if request.method == 'POST':
        del_prod_list = request.form.getlist("sel_prod")  # 从表单中获取删除记录商品的id列表
        username = session.get('username')
        user = User.query.filter(User.username == username).first()
        user_browse_list = user.browse_list.split('_')  # 获取数据库中浏览记录的列表
        for del_prod in del_prod_list:
            if del_prod in user_browse_list:
                user_browse_list.remove(del_prod)
        while '' in user_browse_list:
            user_browse_list.remove('')
        # 以下在数据库中重新建立浏览记录
        user.browse_list = ""
        for prod in user_browse_list:
            user.browse_list = user.browse_list + '_' + prod
        # 以下从数据库中读取浏览记录中的商品信息
        prod_list = []
        for item_id in user_browse_list:
            item_obj = Product.query.filter(and_(Product.id == int(item_id), Product.identity_ok)).first()
            if item_obj is not None:
                prod_list.append(item_obj)
        prod_list.reverse()  # 最近浏览的商品，放在最前面
        db.session.commit()
        if user_browse_list:
            return render_template('del_my_browse.html', prod_list=prod_list, username=user.username)
        else:
            return render_template('my_browse.html', prod_list=prod_list, username=user.username)


    # 以下为初次从查看浏览记录页面切换到编辑浏览页面的部分
    # 初次进入编辑页面，从数据库读取浏览记录并显示
    else:
        username = session.get('username')
        user = User.query.filter(User.username == username).first()

        prod_list = []  # 如果浏览记录为空，则返回空列表
        if user.browse_list is not None:  # 如果浏览记录不为空，添加列表内容
            browse_list = user.browse_list.split('_')

            while '' in browse_list:
                browse_list.remove('')
            for item_id in browse_list:
                item_obj = Product.query.filter(and_((Product.id == int(item_id)), Product.identity_ok)).first()
                if item_obj is not None:
                    prod_list.append(item_obj)
            prod_list.reverse()  # 最近浏览的商品，放在最前面

        return render_template('del_my_browse.html', prod_list=prod_list, username=user.username)


# 9. 添加收藏
@store_app.route('/add_my_collect/<item_id>', methods=['GET', 'POST'])
@login_required
def add_my_collect(item_id):
    item = Product.query.filter_by(id=item_id).first()  # 取得要查看的商品
    # 将商品id添加到collect_list中
    username = session.get('username')
    user = User.query.filter(User.username == username).first()
    seller=User.query.filter(User.username==item.uploader_name).first()

    if user is not None:
        if user.collect_list is None:
            user.collect_list = str(item_id)

        else:
            item_collect_list = user.collect_list.split("_")
            if str(item_id) in item_collect_list:
                # 如果之前存在，那么将其删除再更新到尾巴
                item_collect_list.remove(str(item_id))
                item_collect_list.append(str(item_id))
            else:  # 如果之前不存在，那么判断已浏览的个数
                if len(item_collect_list) >= 40:
                    item_collect_list.pop(0)
                item_collect_list.append(str(item_id))

            user.collect_list = ""
            for item_collect in item_collect_list:
                user.collect_list = user.collect_list + "_" + item_collect

        db.session.commit()

    return render_template('show_item.html', key_word='0', item=item, user_id=user.id,seller_id=seller.id,product_id=item_id,username=session.get('username'), isCollect=1)


# 10 .查看收藏夹
@store_app.route('/mycollect', methods=['GET', 'POST'])
@login_required
def my_collect():
    username = session.get('username')
    user = User.query.filter(User.username == username).first()

    prod_list = []  # 如果收藏夹为空，则返回空列表
    if user.collect_list is not None:  # 如果收藏列表不为空，添加列表内容
        collect_list = user.collect_list.split('_')

        while '' in collect_list:
            collect_list.remove('')
        # ps：我在测试的时候，list里面出现了空元素''，debug之后，现在改正了，不会出现空元素
        # 加入这句话为了以防万一
        for item_id in collect_list:
            item_obj = Product.query.filter(and_((Product.id == int(item_id)), Product.identity_ok)).first()
            if item_obj is not None:
                prod_list.append(item_obj)

        prod_list.reverse()  # 最近添加收藏的商品，放在最前面
    return render_template('my_collect.html', prod_list=prod_list, username=user.username)


#   11.删除收藏夹收藏记录
#   原理跟删除浏览记录一样

@store_app.route('/edit_my_collect', methods=['GET', 'POST'])
@login_required
def del_my_collect():
    if request.method == 'POST':
        del_prod_list = request.form.getlist("sel_prod")  # 从表单中获取删除记录商品的id列表
        username = session.get('username')
        user = User.query.filter(User.username == username).first()
        user_collect_list = user.collect_list.split('_')  # 获取数据库中收藏夹的列表
        #if del_prod in del_prod_list:
        for del_prod in del_prod_list:
            if del_prod in user_collect_list:
                user_collect_list.remove(del_prod)
        while '' in user_collect_list:
            user_collect_list.remove('')
        # 以下在数据库中重新建立浏览记录
        user.collect_list = ""
        for prod in user_collect_list:
            user.collect_list = user.collect_list + '_' + prod
        # 以下从数据库中读取浏览记录中的商品信息
        prod_list = []
        for item_id in user_collect_list:
            item_obj = Product.query.filter(and_((Product.id == int(item_id)), Product.identity_ok)).first()
            if item_obj is not None:
                prod_list.append(item_obj)
        prod_list.reverse()  # 最近浏览的商品，放在最前面
        db.session.commit()
        if user_collect_list:
            return render_template('del_my_collect.html', prod_list=prod_list, username=user.username)
        else:
            return render_template('my_collect.html', prod_list=prod_list, username=user.username)

    # 以下为初次从查看浏览记录页面切换到编辑浏览页面的部分
    # 初次进入编辑页面，从数据库读取浏览记录并显示
    else:
        username = session.get('username')
        user = User.query.filter(User.username == username).first()

        prod_list = []  # 如果收藏夹为空，则返回空列表
        if user.collect_list is not None:
            collect_list = user.collect_list.split('_')

            while '' in collect_list:
                collect_list.remove('')
            for item_id in collect_list:
                item_obj = Product.query.filter(and_((Product.id == int(item_id)), Product.identity_ok)).first()
                if item_obj is not None:
                    prod_list.append(item_obj)
            prod_list.reverse()  # 最近浏览的商品，放在最前面

        return render_template('del_my_collect.html', prod_list=prod_list, username=user.username)

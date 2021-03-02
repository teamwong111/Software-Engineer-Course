# 任何测试的用例函数，需以test_作为前缀
# 测试方法是，在项目目录（而非test目录）下pytest -v
# 需要首先install pytest库

# 建议测试的时候少测试或不测试那个reset（在那个test前面加上字母前缀），不要重复给ljl邮箱发邮件，烦死啦烦死啦烦死啦！！

import os
import tempfile
import pytest

import app

# 产生一个client固件
@pytest.fixture
def client():
    with app.app.test_client() as client:
        ## 这里每次执行一个测试用例的时候，都先把数据库清空
        with app.app.app_context():
            app.db.drop_all()
            app.create_db()
        yield client


# 测试数据库为空的时候，是否有商品
def test_empty_db(client):
    """Start with a blank database."""

    rv = client.get('/')
    str = '暂时还没有商品'
    str = str.encode()
    assert str in rv.data


# 测试注册
## 首先写一个注册
def regist(client, username, password1, password2, email):
    return client.post('/regist',data=dict(username=username,password1=password1,password2=password2,email=email),follow_redirects=True)
## 测试注册
def test_regist(client):
    ### 注册成功的情况
    str = '注册成功'
    rv = regist(client, 'ljl', '1', '1', '1021278241@qq.com')
    str = str.encode()
    assert str in rv.data
    ### 两次密码不同的注册情况
    str = '两次密码不相同'
    rv = regist(client, 'lxy', '666', '777', 'lijialin0222@163.com')
    str = str.encode()
    assert str in rv.data
    ### 与已有账号用户名相同的注册情况
    str = '该用户名或邮箱已被注册'
    rv = regist(client, 'ljl', '666', '666', 'lijialin0222@163.com')
    str = str.encode()
    assert str in rv.data
    ### 与已有账号邮箱相同的注册情况
    str = '该用户名或邮箱已被注册'
    rv = regist(client, 'lxy', '666', '666', '1021278241@qq.com')
    str = str.encode()
    assert str in rv.data
    ### 用户名为空的情况
    str = '用户名长度必须在1-30个字符内'
    rv = regist(client, '', '666', '666', 'lijialin0222@163.com')
    str = str.encode()
    assert str in rv.data
    ### 密码为空的情况
    str = '密码长度必须在1-30个字符内'
    rv = regist(client, 'lxy', '', '', 'lijialin0222@163.com')
    str = str.encode()
    assert str in rv.data
    ### 邮箱格式错误的情况
    str = '邮箱格式不正确'
    rv = regist(client, 'lxy', '666', '666', 'lbynb')
    str = str.encode()
    assert str in rv.data
    ### 使用管理员账号的情况
    str = '这是管理员账号'
    rv = regist(client, 'admin1', '666', '666', 'lijialin0222@163.com')
    str = str.encode()
    assert str in rv.data
    

# 测试登录与注销
## 首先写一个登录
def login(client, username, password):
    return client.post('/login',data=dict(username=username,password=password),follow_redirects=True)
## 首先写一个注销
def logout(client):
    return client.get('/logout',follow_redirects=True)
## 测试登录和注销
def test_login_and_logout(client):
    ### 首先注册
    regist(client, 'ljl', '1', '1', '1021278241@qq.com')
    ### 测试登录成功
    rv = login(client, 'ljl','1')
    str = '成功登录'
    str = str.encode()
    assert str in rv.data
    ### 测试注销成功
    rv = logout(client)
    str = '已注销'
    str = str.encode()
    assert str in rv.data
    ### 测试用户名不存在
    rv = login(client, 'lxy','1')
    str = '错误的用户名或密码'
    str = str.encode()
    assert str in rv.data
    ### 测试密码错误
    rv = login(client, 'ljl','666')
    str = '错误的用户名或密码'
    str = str.encode()
    assert str in rv.data

# 测试修改密码
## 修改密码
def change(client, password0, password1, password2):
    return client.post('/change', data=dict(password0=password0, password1=password1, password2=password2),follow_redirects=True)
## 测试修改密码
def test_change(client):
    ### 首先注册一个用户，并且登录
    regist(client, 'ljl', '1', '1', '1021278241@qq.com')
    login(client, 'ljl','1')
    ### 测试原密码错误
    rv = change(client, '123','666', '666')
    str = '原密码错误'
    str = str.encode()
    assert str in rv.data
    ### 测试两次新密码不同
    rv = change(client, '1','666', '777')
    str = '两次密码输入不相同'
    str = str.encode()
    assert str in rv.data
    ### 测试新密码为空
    rv = change(client, '1','', '')
    str = '密码长度必须在1-30个字符内'
    str = str.encode()
    assert str in rv.data

# 测试找回密码
##忘记密码
def reset(client, name, email):
    return client.post('/reset', data=dict(name=name,email=email),follow_redirects=True)
## 找回密码
def reset_(client, password1, password2):
    return client.post('/reset_/<token>', data=dict(password1=password1, password2=password2),follow_redirects=True)
def test_reset(client):
    ### 首先注册一个账号
    regist(client, 'ljl', '1', '1', '1021278241@qq.com')
    ### 用户名错误
    rv = reset(client, 'lxy','1021278241@qq.com')
    str = '用户名或邮箱输入错误'
    str = str.encode()
    assert str in rv.data
    ### 邮箱错误
    #rv = reset(client, 'ljl','lijialin0222@163.com')
    str = '用户名或邮箱输入错误'
    str = str.encode()
    assert str in rv.data
    ### 忘记密码成功
    rv = reset(client, 'ljl','1021278241@qq.com')
    str = '成功发送验证邮件'
    str = str.encode()
    assert str in rv.data
    ### 测试找回密码，两次密码不相同
    ### 这里应该有东西的，但是我不会测试动态的URL

# 这里应该是测试的身份认证，但是由于图片出了问题，不会测了。。
# # 测试身份认证
# ## 身份认证
# def identity(client, file):
#     return client.post('/identity',data=dict(file=file),follow_redirects=True)
# ## 测试身份认证
# def test_identity(client):
#     ### 首先注册一个用户，并且登录
#     regist(client, 'ljl', '1', '1', '1021278241@qq.com')
#     login(client, 'ljl','1')
#     rv = identity(client, file="http://wx2.sinaimg.cn/mw690/ac38503ely1fesz8m0ov6j20qo140dix.jpg")
#     str = '上传成功'
#     str = str.encode()
#     assert str in rv.data

# 测试修改用户名
## 修改用户名
def changeName(client, username):
    return client.post('/changeName', data=dict(username=username), follow_redirects=True)
def test_changeName(client):
    ### 首先注册一个用户，并且登录
    regist(client, 'ljl', '1', '1', '1021278241@qq.com')
    regist(client, 'lxy', '1', '1', 'lijialin0222@163.com')
    login(client, 'ljl','1')
    ### 测试修改用户名重名的情况
    rv = changeName(client, 'lxy')
    str = '用户名已存在'
    str = str.encode()
    assert str in rv.data
    ### 测试修改的用户名是管理员用户名的时候
    rv = changeName(client, 'admin1')
    str = '这是管理员账号'
    str = str.encode()
    assert str in rv.data
    ### 测试修改的用户名为空的情况
    rv = changeName(client, '')
    str = '用户名长度必须在1-30个字符内'
    str = str.encode()
    assert str in rv.data
    ### 测试修改成功的时候
    rv = changeName(client, 'ljl666')
    str = '昵称修改成功'
    str = str.encode()
    assert str in rv.data

# 测试封号部分
## 封号
def admin_account(client, username, is_pass):
    return client.post('/admin_account', data=dict(username=username,is_pass=is_pass), follow_redirects=True)
def test_admin_account(client):
    regist(client, 'ljl', '1', '1', '1021278241@qq.com')
    login(client, 'admin3','password3')
    ### 测试封号成功
    rv = admin_account(client, 'ljl', 'yes')
    str = '封号成功'
    str = str.encode()
    assert str in rv.data
    ### 测试重复封号
    rv = admin_account(client, 'ljl', 'yes')
    str = '该账号已被封禁'
    str = str.encode()
    assert str in rv.data
    ### 测试解除封号成功
    rv = admin_account(client, 'ljl', 'no')
    str = '解封成功'
    str = str.encode()
    assert str in rv.data
    ### 测试重复解除封号
    rv = admin_account(client, 'ljl', 'no')
    str = '该账号未被封禁'
    str = str.encode()
    assert str in rv.data
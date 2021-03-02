import os

#获得绝对路径
basedir = os.path.abspath(os.path.dirname(__file__))


#用来初始化app
class Config():
    #设置密钥，保证Session, Cookies的安全，os.urandom随机生成
    SECRET_KEY = 'p\xcewyS\x14P\x08\xff\xdb\xd7\x89U\x98\xe8I\xc1\xf1\xa2\x85?\x1ch\xec'
    #数据库路径
    SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(
        basedir, 'data.sqlite')
    SQLALCHEMY_TRACK_MODIFICATIONS = True

    MAIL_SERVER = 'smtp.163.com'
    MAIL_PORT = 465
    #MAIL_USE_TLS = True
    MAIL_USE_SSL = True
    MAIL_USERNAME = 'buybuyteam@163.com'
    MAIL_PASSWORD = 'RPCXPPJUFKSTSVXB'
# find_av_by_face
难道你就不想找到你喜欢的明星，对应的av女优吗？


# 如何使用
系统主入口是main.py文件，系统集成了2套检测方法，分别是：  

## 百度AI接口
先去申请一个[百度AI平台](http://ai.baidu.com/)的账号，创建一个应用，使用人脸对比接口。这样就可以获得一对密钥，输入到项目的config.conf文件中。这个文件可能没有提交上git，大家自行创建。
```
[baidu]
client_id = UGBkTfzWFLGLeR大概是这样
client_secret = ZMQTUQCgiF大概是这样

[db]
path = 大概是这样/db/mydb.sqlite3
```
人脸识别率高，但是由于用的是免费接口，并发控制最大是2，一万张图片大概需要1小时  
```
face = FaceBaiDu()
```

## dlib本地检测框架
人脸识别率中，首次初始化一万张图片，需要40分钟左右，之后的二次请求，就会非常快，  
但是opencv的人脸检测能力实在是有待观望，一万张图片大概有600多张识别不出人脸。  
```
face = FaceDlib()
```


## 数据库
目前爬取了1万张av女优头像图片  
[点击下载数据库](https://pan.baidu.com/s/11xLcvmSjYIG3cyR7voux_w)  
为了保护某网站健康稳定发展，字段里屏蔽了爬取的网站域名


## 如何安装dlib (windows系统)
先安装cmake  
```
pip install cmake
```
再安装dlib  

1. 访问[dlib官网](http://dlib.net/)，点击左下角的download，下载源码到本地  
2. 解压到本地，发现里面有个setup.py  
3. 在当前文件路径打开命令行，执行`python setup.py install`

如果最后不成功的话，继续往下看
1. 提示`window sdk 8.1 不存在`  
如果你有装到Visual Studio 2015，并且在dlib解压的目录里发现`\build\temp.win32-3.6\Release\CMakeFiles\3.13.3`这个路径，
并且里面有个文件`VCTargetsPath.vcxproj`，用vs加载它，vs一般会提示你安装C++套件，安装完就可以再次尝试安装dlib。  
目前来看，微软官网已经没有`windows sdk 8.1`下载，只有`windows sdk 10`，装这个10是没用的，按照错误提示的说法，如果你想切换到10来编译的话，
也是需要加载`VCTargetsPath.vcxproj`来改它的属性，在属性里改为用10来编译。



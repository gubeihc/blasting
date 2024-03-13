# 程序说明

工具主要是为了方便在面对web后台进行爆破测试的时候，用户名和密码是加密的情况下
如果单纯分析js来进行爆破测试时间成本会比较多，

这里呢就采用模拟浏览器通过调用js来直接写入账号密码进行请求，来快速达到测试效果。

# 添加交流群

QQ群 923369496


![image](https://github.com/gubeihc/blasting/blob/main/image/qq.pic.jpg)



# 更新


最新在土司学习了一下通过cdp 协议打断点 直接调用加密函数，感觉不错就添加了一下

使用案例
https://www.t00ls.com/thread-69976-1-1.html

### 爆破模式：完全模仿Burp Site

```
sniper:狙击手
```

```
ram:攻城锤
```

```
fork:草叉模式
```

```
bomb:集束炸弹
```

```
jietu:截图
截图模式 采用的也是 sniper:狙击手
```

## 程序优点

优点1：针对网站后台用户名密码加密无需分析js即可爆破请求。

优点2：采用通用特征方式识别用户名和密码进行提交请求。

优点3：通过内置大佬ddddocr库可以进行存在验证码后台爆破。

优点4：通过监听请求数据可以做到验证码错误重试功能。

优点5：可以对大量不同登录系统进行批量爆破测试并截图。

优点6：新添加cdp模式，可以使用工具直接爆破也可以配合burp的autodecoder插件做到burp调试明文实际发包密文传输。





### 源码使用需要安装浏览器

建议更换一下源
pip config set global.index-url https://mirrors.aliyun.com/pypi/simple/

python3 -m playwright install

## 演示视频
链接: 链接: https://pan.baidu.com/s/1MVjXVZFB_mPND0SYZRCnIw 提取码: ch3n



# 三种请求模式。 自动、手动、cdp爆破，

## 自动模式针对标准后台登录网站 输入账户密码字典就可以爆破

![image](https://github.com/gubeihc/blasting/blob/main/image/zd.png)


## 手动模式的话就需要填入 用户 密码 登录按钮 如果有验证码就填入验证码的xpath 路径  
![image](https://github.com/gubeihc/blasting/blob/main/image/sd.png)

## cdp模式需要配合burp使用，采用aiohttp来进行发包，cdp协议来远程调用加密函数

![image](https://github.com/gubeihc/blasting/blob/main/image/cdp.png)


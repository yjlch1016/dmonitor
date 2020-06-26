# dmonitor  
基于Django的轻量级生产环境接口监控平台  
dmonitor即为django+monitor的缩写  

***
# 模型  
5张表   
微服务表一对多用例表  
用例表一对多步骤表  
步骤表一对多运行结果表  
微服务表一对一环境配置表  

|  表   | 字段  |
|  ----  | ----  |
| 微服务表  | 微服务开关、钉钉开关、邮件开关、微服务简介、创建时间、修改时间 |
| 用例表  | 用例名称、用例开关、钉钉开关、邮件开关、创建时间、修改时间 |
| 步骤表  | 步骤名称、请求方式、接口路径、请求体、请求头、请求参数、预期的响应时间、预期的响应代码、预期的响应结果、正则、创建时间、修改时间 |
| 运行结果表  | 是否通过、失败原因、运行时间、实际的响应时间、实际的响应代码、实际的响应结果 |
| 环境配置表  | 域名、创建时间、修改时间 |

***
# 本地调试  
`python manage.py collectstatic`  
复制xadmin静态文件  

`python manage.py makemigrations`  
激活模型  

`python manage.py migrate`  
迁移  

`python manage.py createsuperuser`  
创建超级管理员账号  
输入账号：admin  
输入邮箱：123456789@qq.com  
输入密码：test123456  
二次确认  

`python manage.py runserver`  
启动服务 

http://127.0.0.1:8000/admin/  
用户名：admin  
密码：test123456

***
# 本地打包  
`docker build -t monitor .`  
monitor为镜像名称，随便取  

`docker run -d --name monitor2020 -p 80:80 mock:latest`  
启动容器  
后台运行  
给容器取个别名monitor2020  
映射80端口  

http://x.x.x.x/admin/  
宿主机的IP地址  
账号：admin  
密码：test123456  

`docker exec -it monitor2020 /bin/bash`  
进入容器内部

`exit`  
退出容器内部

`docker stop monitor2020`  
停止容器  

`docker rm monitor2020`  
删除容器  

***
# 公网访问地址  
http://www.monitor.com/admin/  
账号：admin  
密码：test123456  

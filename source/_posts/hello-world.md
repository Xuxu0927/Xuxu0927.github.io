---
title: Hello World
date: 2026-05-03
---

# 快速入门指南

欢迎来到我的博客！本文是 Hexo 博客框架的快速入门指南，介绍如何创建文章、启动本地服务器、生成静态文件以及部署到远程站点。

## 创建新文章

``` bash
$ hexo new "My New Post"
```

More info: [Writing](https://hexo.io/docs/writing.html)

## 启动本地服务器

``` bash
$ hexo server
```

More info: [Server](https://hexo.io/docs/server.html)

## 生成静态文件

``` bash
$ hexo generate
```

More info: [Generating](https://hexo.io/docs/generating.html)

## 部署到远程站点

``` bash
$ hexo deploy
```

More info: [Deployment](https://hexo.io/docs/one-command-deployment.html)



## 代码示例：分数评级

以下是一个简单的 Python 示例，演示如何根据分数输出对应的等级：

```python
score = int(input('输入分数:\n'))
if score >= 90:
    grade = 'A'
elif score >= 60:
    grade = 'B'
else:
    grade = 'C'

print('%d 属于 %s' % (score, grade))
```


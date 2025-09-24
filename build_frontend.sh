#!/bin/bash

# 前端项目构建和打包脚本
# 用于部署到CentOS服务器

echo "开始构建前端项目..."

# 进入前端项目目录
cd csgo-dashboard

# 安装依赖
echo "安装前端依赖..."
npm install

# 构建生产版本
echo "构建生产版本..."
npm run build

# 检查构建是否成功
if [ $? -eq 0 ]; then
    echo "前端构建成功！"
    
    # 创建部署包
    echo "创建部署包..."
    cd ..
    
    # 创建部署目录
    mkdir -p deploy/frontend
    
    # 复制构建文件
    cp -r csgo-dashboard/build/* deploy/frontend/
    
    # 创建压缩包
    tar -czf csgo-frontend-$(date +%Y%m%d_%H%M%S).tar.gz -C deploy frontend
    
    echo "前端部署包创建完成: csgo-frontend-$(date +%Y%m%d_%H%M%S).tar.gz"
    echo "请将此文件上传到服务器并解压到nginx的web目录"
    
else
    echo "前端构建失败！"
    exit 1
fi
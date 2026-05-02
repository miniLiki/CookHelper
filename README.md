# 项目名称

> 一句话描述你的项目

## 📝 项目简介

详细介绍你的项目:
- 解决什么问题？
- 有什么特色功能？
- 适用于什么场景？

## ✨ 核心功能

- [ ] 功能1:描述
- [ ] 功能2:描述
- [ ] 功能3:描述

## 🛠️ 技术栈

**前端:**
- Next.js 14 (React框架)
- Tailwind CSS (样式框架)
- Zustand (状态管理)
- Framer Motion (动画)

**后端:**
- Python 3.11 + Flask
- Neo4j (图数据库)
- Milvus (向量数据库)
- 图RAG + 混合检索

**部署:**
- Docker + Docker Compose
- Nginx (反向代理)

## 🚀 快速开始
### 📋 前置要求

✅ **Docker Desktop** - [下载安装](https://www.docker.com/products/docker-desktop/)
✅ **Node.js 18+** - [下载安装](https://nodejs.org/) (可选，仅开发时需要)

### 🎯 一键启动

**Windows 用户（推荐）:**
```bash
# 1. 克隆项目
git clone https://github.com/miniLiki/CookHelper.git
cd CookHelper

# 2. 双击运行或命令行启动
start.bat
```

**Linux/macOS 用户:**
```bash
# 1. 克隆项目
git clone https://github.com/miniLiki/CookHelper.git
cd CookHelper

# 2. 给脚本执行权限并启动
chmod +x start.sh stop.sh
./start.sh
```
### 🌐 访问应用

启动完成后，脚本会自动打开浏览器，或手动访问：

- **🏠 应用首页**: http://localhost
- **⚛️ 前端**: http://localhost:3000
- **🐍 后端API**: http://localhost:8000
- **📊 Neo4j**: http://localhost:7474 (neo4j/all-in-rag)
- **🗄️ Milvus**: http://localhost:9001 (minioadmin/minioadmin)

## 🛑 停止服务

```bash
# 停止所有服务
stop.bat        # Windows
./stop.sh       # Linux/macOS

# 或者直接使用 Docker Compose
docker-compose down

# 完全重置（清除所有数据）
docker-compose down -v
```

## 📝 常用命令

```bash
# 查看所有服务状态
docker-compose ps

# 查看特定服务日志
docker-compose logs -f backend
docker-compose logs -f frontend

# 重启特定服务
docker-compose restart backend

# 完全重置（清除所有数据）
docker-compose down -v
```

## 📖 使用示例

展示如何使用你的项目，最好包含代码示例和运行结果。

## 🎯 项目亮点

- 亮点1:说明
- 亮点2:说明
- 亮点3:说明

## 📊 性能评估

如果有评估结果，展示在这里:
- 准确率:XX%
- 响应时间:XX秒
- 其他指标

## 🔮 未来计划

- [ ] 待实现的功能1
- [ ] 待实现的功能2
- [ ] 待优化的部分

## 🤝 贡献指南

欢迎提出Issue和Pull Request！

## 📄 许可证

本项目采用 [MIT License](./LICENSE) 开源协议。

## 👤 作者
- Email: 2250085474@qq.com

## 🙏 致谢

本项目的开发得益于以下开源项目和教程：

### 📚 教程项目
- **[Datawhale/all-in-rag](https://github.com/datawhalechina/all-in-rag)** - 大模型应用开发实战：RAG技术全栈指南
  - 本项目是该教程的完整实战案例，展示了RAG技术的实际应用
  - 涵盖数据处理、索引构建、检索优化、生成集成等完整技术栈
  - 通过实际的美食推荐场景，帮助学习者理解图RAG技术的实现细节

### 🍳 菜谱数据
- **[Anduin2017/HowToCook](https://github.com/Anduin2017/HowToCook)** - 程序员在家做饭方法指南
  - 本项目的菜谱数据主要来源于这个优秀的开源项目
  - 该项目用程序员的思维整理了大量实用的菜谱，格式规范、描述清晰
  - 感谢 [@Anduin2017](https://github.com/Anduin2017) 和所有贡献者们的无私分享

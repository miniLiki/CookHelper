# 项目名称

CookHelper (cooker) - AI 美食推荐助手
![界面](./view1.png)
![聊天界面](./view2.png)

## 📝 项目简介

一个基于图 RAG + 向量检索的智能烹饪助手，面向“今天吃什么”场景，提供菜谱推荐、问答交互和分步骤烹饪指导。

项目主要解决：
- 每天做饭决策困难（不知道吃什么）
- 菜谱检索效率低（关键词不好找、信息分散）
- 新手做菜缺少结构化指导（步骤、时长、食材比例）

适用场景：
- 家庭日常做饭
- 新手学习烹饪
- 想通过自然语言快速获得菜谱建议

## ✨ 核心功能

- [x] 智能推荐：基于图数据库 + 向量数据库的混合检索推荐
- [x] 对话问答：支持自然语言提问与连续会话
- [x] 菜谱详情页：展示食材、步骤、时长、标签等信息
- [x] 一键部署：`start.sh` / `start.bat` 启动完整服务
- [x] 前端可定制：支持自定义 Logo 和背景图

## 🛠️ 技术栈

**前端:**
- Next.js 14 (React框架)
- TypeScript
- Tailwind CSS
- Zustand
- Framer Motion

**后端:**
- Python 3.11 + Flask
- Neo4j (图数据库)
- Milvus (向量数据库)
- 图RAG + 混合检索

**部署:**
- Docker + Docker Compose
- Nginx (反向代理)
- MinIO + etcd（Milvus依赖）

## 🚀 快速开始
### 📋 前置要求

- Docker Desktop（必需）
- Node.js 18+（可选，仅本地前端开发需要）

### 🎯 一键启动

**Windows 用户（推荐）:**
```bash
# 1. 克隆项目
git clone https://github.com/miniLiki/CookHelper.git
cd cookhelper

# 2. 双击运行或命令行启动
start.bat
```

**Linux/macOS 用户:**
```bash
# 1. 克隆项目
git clone https://github.com/miniLiki/CookHelper.git
cd cookhelper

# 2. 给脚本执行权限并启动
chmod +x start.sh stop.sh
./start.sh
```

如果你本地目录为 `/home/ly/cookhelper`，可直接在该目录执行：
```bash
cd /home/ly/cookhelper
./start.sh
```

### 🌐 访问应用

启动完成后，脚本会自动打开浏览器，或手动访问：

- **🏠 应用首页**: http://localhost
- **⚛️ 前端**: http://localhost:3000
- **🐍 后端API**: http://localhost:8000
- **📊 Neo4j**: http://localhost:7474 (neo4j/all-in-rag)
- **🗄️ Milvus/MinIO 控制台**: http://localhost:9001 (minioadmin/minioadmin)

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
docker-compose logs -f nginx

# 重启特定服务
docker-compose restart backend

# 完全重置（清除所有数据）
docker-compose down -v
```

## 📖 使用示例

```bash
# 1) 启动项目
cd /home/ly/cookhelper
./start.sh

# 2) 打开首页
# http://localhost

# 3) 进入聊天页，输入示例问题
# “今天晚餐吃什么？”
# “推荐一道30分钟内能完成的家常菜”
```

前端样式修改示例：
```bash
cd /home/ly/cookhelper/frontend
npm install
npm run dev
```

## 🎯 项目亮点

- 图检索 + 向量检索组合，兼顾语义匹配和结构关系
- 提供容器化一键启动，降低本地部署门槛
- UI 支持快速个性化：
  - Logo：`frontend/public/logo.png`
  - 背景：`frontend/public/beijing.jpg`

## 📊 性能评估

当前仓库未提供统一 benchmark 脚本，建议按以下维度自行评估：
- 首次容器启动时长
- 推荐响应时间（后端 API）
- 多轮对话稳定性

## 🔮 未来计划

- [ ] 增加用户偏好记忆与推荐个性化
- [ ] 增加更多菜系与饮食限制（减脂/素食/低盐）
- [ ] 增加自动化测试与 CI 流程

## 🤝 贡献指南

欢迎提出 Issue 和 Pull Request。

建议流程：
1. Fork 本仓库
2. 新建功能分支
3. 提交修改并附变更说明
4. 发起 PR

## 📄 许可证

本项目采用 [MIT License](./LICENSE) 开源协议。

## 👤 作者
- GitHub: https://github.com/miniLiki
- Email: 2250085474@qq.com

## 🙏 致谢

本项目的开发得益于以下开源项目和教程：

### 📚 教程项目
- **[Datawhale/all-in-rag](https://github.com/datawhalechina/all-in-rag)** - 大模型应用开发实战：RAG技术全栈指南
  - 本项目是该教程的完整实战案例，展示了RAG技术的实际应用
  - 涵盖数据处理、索引构建、检索优化、生成集成等完整技术栈

### 🍳 菜谱数据
- **[Anduin2017/HowToCook](https://github.com/Anduin2017/HowToCook)** - 程序员在家做饭方法指南
  - 本项目菜谱数据主要来源于该开源项目
  - 感谢 [@Anduin2017](https://github.com/Anduin2017) 及所有贡献者

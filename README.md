# metricd · 指标口径注册与一致性检查中心

> 在线教育「微光课堂」数据治理委员会的口径台账：把指标定义、版本 DSL、依赖关系和一致性巡检放进一个可运行的全栈系统。

## 1. 真实场景

- **客户**：微光课堂（在线教育）数据治理委员会，6 人；4 个业务团队各自维护指标。
- **现状**：指标口径散落在 Confluence 页面与 SQL 注释里，同名指标靠人问。
- **三个痛点**
  1. 「活跃用户」有三个口径，销售看板、内容看板和 AB 实验报表互相对不上；
  2. 指标改口径没人知道影响哪些看板，只能事后被业务追问；
  3. 指标依赖里藏着环形引用，调度器半夜死循环。
- **上下游**：上游埋点库/订单库 → 本系统注册 DSL、版本、依赖并跑一致性检查 → 下游 BI 看板与 AB 平台读取「当前版本 + 影响面」。
- **一天的工作剧本**：分析员登录 → 指标目录搜 `active_users` → 打开三版本对比 → 运行一致性检查 → 看到 3 条 high 冲突 → 在 DSL 编辑器改 `window` 并重新解析 → 依赖图定位两处环 → 负责人尝试改别域指标被 403 → 导出影响面 CSV 给委员会。

## 2. 角色与权限

| 角色 | 账号 | 主要页面 | 权限 | 典型动作 |
| --- | --- | --- | --- | --- |
| `admin` 治理管理员 | `admin@metric.local` | 全部 | 域/团队/检查/冲突处理；可改任意指标 | 发起检查、确认/解决冲突、转移指标归属 |
| `owner` 指标负责人 | `owner@metric.local`（增长组） | 目录/详情/DSL/依赖/检查 | 只能改**本团队负责**的指标与版本 | 提交新版本 DSL、维护 `using` 依赖 |
| `analyst` 分析员 | `analyst@metric.local` | 全部页面（只读） | 只读目录/依赖图/冲突；可发起只读分析型检查批次，不能改指标 | 查口径、跑检查、看影响面、导 CSV |

密码统一 **`Demo@2026`**（写进 seed，也写在这里；`.env` 中的 `SEED_DEMO=true` 启动时自动跑一次幂等 seed）。

## 3. 核心实体（6）

`MetricDefinition`（指标 key/域/负责团队/状态）· `MetricVersion`（版本号/DSL/五元组/生效时间，可跨团队）· `MetricDependency`（指标→指标 / 指标→物理表）· `ConsistencyCheck`（批次/状态/分数/汇总）· `ConflictFinding`（冲突维度/严重度/证据/影响面）· `OwnerTeam`（团队/域/负责人/SLA）。另有 `User` 与 `AuditLog` 作为横切支撑。

## 4. 两个后端真算算法

### 4.1 指标 DSL 解析 + 依赖图

`backend/app/algorithms/dsl_parser.py` 用纯 Python 解析：

```
metric active_users = count(distinct user_id) from fact_visit
  where date >= today-7 filter platform in ('ios','android')
  grain day window 7d using (new_signups)
```

- 输出五元组 `(agg, measure, filter 集合, window, grain)` + 源码 token 位置（编辑器高亮）+ `using` 依赖预览；
- `where date >= today-N` 在缺少 `window` 时推导窗口；非法聚合/粒度/自依赖返回带 offset 的语义错误；
- `backend/app/algorithms/graph.py`：Kahn 拓扑排序（依赖在前）、Tarjan SCC 找环并给出环路径、孤儿指标检测（无下游消费且无 BI 看板）、分层坐标供手写 SVG。

### 4.2 口径冲突检测 + 影响面

`backend/app/algorithms/conflict.py`：

- 同名指标多版本按五元组两两比较，差异维度严重度：`grain/filter/agg = high`、`window = medium`、`measure = low`，多维差异归为 `multi`；
- 一致性分数 `100 × (1 − Σ各对差异权重 / (对比对数 × 12))`，权重 high=3 / medium=2 / low=1；
- 影响面 = 反向依赖闭包（受影响指标）+ 这些指标登记的 BI 看板，随 finding 落库并可导出 CSV。

批次执行链路：`POST /checks`（backend 创建 pending 批次，扣减每日检查配额，Redis 加 scope 锁）→ Celery worker `metricd.run_consistency_check` → 重新解析全部 DSL、更新版本五元组、写 `ConflictFinding` 与批次汇总 → 前端轮询显示分数/环/孤儿/冲突。

## 5. 6 个页面

1. `/login` 登录（索引卡 + 三角色快捷填充）
2. `/catalog` 指标目录（域分组 + 搜索 + 状态徽标 + 五元组速览）
3. `/metrics/:id` 指标详情与版本历史（五元组比对、依赖、影响面）
4. `/metrics/:id/dsl` DSL 编辑器（实时后端解析 + token 高亮 + 依赖预览 + 保存新版本）
5. `/graph` 依赖图（手写 SVG 分层布局，环红色虚线、孤儿虚线，点击看影响面）
6. `/checks` 一致性检查与冲突详情（分数、冲突表、环/孤儿、CSV 导出、管理员可确认/解决）

## 6. 快速启动

```bash
cp .env.example .env
docker compose up -d --build
# 等待 5 个服务 healthy
docker compose ps
```

访问：

- 前端 <http://localhost:18223>
- 后端 API <http://localhost:19223/docs>
- MySQL `localhost:17723`（库 `metricd_db`）

手动重跑 seed（幂等）：

```bash
docker compose exec -T backend python -m scripts.seed_demo
# 输出一行 SEED_SUMMARY {"conflict_finding":5,...}；连跑两次数字一致
```

## 7. 技术栈

| 层 | 选型 |
| --- | --- |
| 前端 | Vue 3 + TypeScript + Vite + Pinia + vue-router；手写 CSS（oklch + 索引卡视觉）；无图表库 |
| 后端 | Python 3.11 + FastAPI + SQLAlchemy 2.0 + Pydantic v2 + PyJWT + Alembic |
| 异步 | Celery 5 + Redis 7（检查批次由 worker 执行） |
| 数据库 | MySQL 8.0（utf8mb4，命名卷持久化） |
| 网关 | Nginx 1.27（`/api/` 反代 backend:8000 + SPA 回落） |

`docker compose` 顶层 `name: metricd`，容器名 `${COMPOSE_PROJECT_NAME:-metricd}-<role>`。

## 8. 目录结构

```
frontend/src/{api,stores,types,components/{common,metric,dependency,check},hooks,pages,router,utils,constants,styles}
backend/app/{routes,controllers,services,models,schemas,middlewares,utils,constants,config,algorithms,tasks}
backend/scripts/seed_demo.py
backend/migrations/（Alembic：alembic.ini + alembic/）
worker/{Dockerfile,entrypoint.sh,healthy.py}
```

## 9. 环境变量（`.env.example`）

`COMPOSE_PROJECT_NAME` `DB_NAME` `DB_USER` `DB_PASSWORD` `DB_ROOT_PASSWORD` `JWT_SECRET` `FRONTEND_PORT` `BACKEND_PORT` `DB_PORT` `REDIS_URL` `ARTIFACT_DIR` `CHECK_DAILY_QUOTA` `RATE_WINDOW_SECONDS` `RATE_WINDOW_MAX` `SEED_DEMO`。后端字段在 `backend/app/config/settings.py` 中同名覆盖。

## 10. 共享枚举出现位置

| 枚举 | 后端 | 前端 |
| --- | --- | --- |
| 角色 `admin/owner/analyst` | `app/constants/roles.py` | `src/constants/roles.ts` |
| 指标状态 `draft/active/deprecated` | `app/constants/metric_status.py` | `src/constants/metricStatus.ts` |
| 冲突维度 `agg/measure/filter/window/grain/multi` + 严重度策略 | `app/constants/conflict_type.py` + `severity.py` | `src/constants/conflictType.ts` + `severity.ts` |
| 检查状态 | `app/constants/check_status.py` | `src/constants/checkStatus.ts` |
| 业务域 | `app/constants/domains.py` | `src/constants/domains.ts` |
| 错误码 | `app/constants/error_codes.py` | `src/constants/errorCodes.ts` |

## 11. 主要 API

所有接口挂载在 `/api` 前缀下（Nginx 与后端直连一致）：`POST /auth/login` · `GET /auth/me` · `GET /metrics` · `GET /metrics/{id}` · `POST /metrics` · `PATCH /metrics/{id}` · `GET/POST /metrics/{id}/versions` · `PATCH /versions/{id}` · `GET /metrics/{id}/compare` · `POST /dsl/parse` · `GET /dependencies/graph` · `GET /metrics/{id}/impact` · `GET/POST /checks` · `GET /checks/latest` · `GET /checks/{id}` · `GET /checks/{id}/impact.csv` · `PATCH /findings/{id}` · `GET /teams` · `GET /audit/recent` · `GET /health`。

## 12. 横切能力

- JWT（8 小时）+ 数据库权威角色；`owner` 跨团队写操作返回 403；
- 审计日志中间件（登录、创建/更新指标与版本、发起检查、冲突处理、导出）；
- 限流（Redis 滑动窗口，写请求）+ 每日检查配额 + 检查 scope 锁。

## 13. 测试与已知差异

测试产物在 `batch-20261110/test-artifacts/gb-550/`（`TESTING.md`、`tests/screenshots.cjs`、`screenshots/`、`logs/`），不随源码目录提交。已知差异见 `TESTING.md` 的「已知差异」章节。

## 14. License

仅供评测演示使用（内部批次 batch-20261110）。

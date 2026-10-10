# 贡献指南

感谢你愿意为 ds-agent 贡献。

## 开发环境

```bash
git clone <your-repo-url> ds-agent
cd ds-agent
python scripts/setup.py --skip-config
.venv/bin/python -m pip install -e ".[dev,admin]"
```

Windows 下虚拟环境路径为 `.venv\Scripts\python.exe`。

## 代码规范

- 使用 `ruff` 检查并格式化：`ruff check src tests`、`ruff format src tests`
- 关键函数必须有类型注解与 docstring
- 新增模块必须 import 无副作用
- 外部调用必须有超时、异常捕获、可读错误
- 日志统一使用 `logging`，禁止 `traceback.print_exc()`

## 测试

```bash
pytest -q
```

测试必须：

- 不依赖 Firefox / DeepSeek / 网络
- 使用 `tests/conftest.py` 中的隔离配置
- 覆盖新增功能的正常路径与错误路径

## 提交前检查

```bash
pre-commit install
pre-commit run --all-files
```

或手动运行：

```bash
ruff check src tests
pytest -q
```

## 安全红线（PR 会被直接拒绝）

- 提交真实 API Key、Token、Cookie、密码、会话 id
- 提交 `config/config.yaml`、`.env`、`_internal/` 或 `workspace/` 内容
- 引入绕过登录 / 验证 / 付费的代码
- 添加批量请求、爬虫、破解相关实现
- 在 README 或代码中暗示与 DeepSeek 官方有关联

## 提交信息

使用简洁的祈使句式，例如：

- `feat: 支持 OpenAI 兼容后端`
- `fix: 修正 web 后端 ds_read 脚本路径`
- `docs: 补充驱动切换说明`

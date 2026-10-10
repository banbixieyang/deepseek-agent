# GitHub 初始化命令

本文件只提供命令，不自动执行 push。请自行审核后再推送。

## 1. 本地初始化

在 `rebuild/` 目录下执行：

```bash
git init
git add .
git status                 # 检查是否有敏感文件被误加
git commit -m "chore: initial commit for ds-agent rebuild"
```

## 2. 检查清单（提交前必做）

```bash
git status --porcelain | grep -E "(config/config.yaml|_internal/|\.env$|\.bak$|\.log$)" || echo "OK: 无敏感文件"
grep -rn "C:\\\\Users\\\\" . --include="*.py" --include="*.md" --include="*.yaml" || echo "OK: 无硬编码用户路径"
grep -rn "sk-" . --include="*.py" --include="*.md" || echo "OK: 无 sk- 前缀 Key"
```

## 3. 创建远程仓库（可选，gh CLI）

```bash
gh repo create ds-agent --public --source=. --remote=origin --description "可审批的本地 Agent 执行器"
```

或手动：在 GitHub 网页新建空仓库，然后：

```bash
git remote add origin <你的仓库地址>
git branch -M main
```

## 4. 推送（本文件不自动执行）

确认无误后再手动执行：

```bash
git push -u origin main
```

## 5. 永不提交的内容

以下由 `.gitignore` 覆盖，请勿手动 `git add -f`：

- `.env`
- `config/config.yaml`
- `_internal/`
- `workspace/*`（仅保留 `workspace/.gitkeep`）
- `*.bak`
- `*.log`
- `__pycache__/`、`*.pyc`、`.venv/`、`dist/`、`build/`

## 6. 建议的 GitHub 仓库设置

- Description：可审批的本地 Agent 执行器；默认走 DeepSeek 官方 API
- Topics：`agent`、`deepseek`、`local-executor`、`approval`
- License：MIT
- 关闭 Issues 中的敏感内容上传，或在 CONTRIBUTING 中提示

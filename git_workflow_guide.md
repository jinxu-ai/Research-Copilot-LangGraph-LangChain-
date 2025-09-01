# 常用 Git 工作流指南

本文件总结了在日常开发中使用 Git/GitHub 的常见工作流，包括命令行、VS Code 与 GitHub Desktop 的操作方式对照。适合个人开发与小团队协作。

---

## 0) 全局设置（只做一次）

```bash
git config --global user.name "你的名字"
git config --global user.email "你的邮箱"
git config --global init.defaultBranch main
```

---

## 1) 同步远程 main（每天开始前）

```bash
git checkout main
git fetch origin
git pull --ff-only origin main
```

- **VS Code**：Source Control → … → Pull  
- **GitHub Desktop**：顶部 `Fetch origin` → `Pull origin`

---

## 2) 新建并切换到功能分支

```bash
git checkout -b feat/rag-eval
```

- **命名约定**：
  - `feat/` 新功能
  - `fix/` 修复
  - `docs/` 文档
  - `chore/` 杂项

---

## 3) 查看状态并暂存文件

```bash
git status
git add app/ui.py chains/synthesize.py
# 或一次性全部：
git add .
```

---

## 4) 本地提交（commit）

```bash
git commit -m "feat(ui): add streamlit panel for parameters"
```

- 推荐 [Conventional Commits] 风格：`type(scope): message`

---

## 5) 推送到远程（push）

```bash
git push -u origin feat/rag-eval
```

---

## 6) 提交合并请求（PR）

- **GitHub 网页端**：Compare & pull request → 填写说明 → Merge  
- **VS Code**：安装 GitHub Pull Requests 扩展  
- **Desktop**：右上角 Create Pull Request 按钮

---

## 7) 合并后收尾

```bash
git checkout main
git pull --ff-only origin main
git branch -d feat/rag-eval
git push origin --delete feat/rag-eval   # 可选
```

---

## 与 main 同步（在功能分支上）

推荐 **rebase**，保持历史干净：

```bash
git checkout feat/rag-eval
git fetch origin
git rebase origin/main
# 解决冲突后继续
git rebase --continue
git push --force-with-lease
```

---

## 撤销与回退

1. 撤销工作区改动：
```bash
git checkout -- path/to/file
```

2. 撤销已暂存：
```bash
git restore --staged path/to/file
```

3. 回退上一次提交但保留改动：
```bash
git reset --soft HEAD~1
```

4. 撤销已推送的错误提交：
```bash
git revert <commit_sha>
git push
```

---

## 查看历史与差异

```bash
git log --oneline --graph --decorate --all
git show HEAD
git diff
git diff --staged
```

---

## 暂存（Stash）

```bash
git stash push -m "WIP: experiment"
git stash list
git stash pop
```

---

## .gitignore 小技巧

- 忽略整个文件夹但保留占位：
```
data/
!data/.gitkeep
notes/
!notes/.gitkeep
```

- 检查为何被忽略：
```bash
git check-ignore -v data/.gitkeep
```

---

## 打标签与发布（可选）

```bash
git tag -a v0.1.0 -m "first demo"
git push origin v0.1.0
```

---

# 常用命令速查表

```bash
# 状态与远程
git status
git remote -v

# 拉取/推送
git fetch origin
git pull --ff-only origin main
git push origin HEAD

# 分支
git branch
git checkout -b feat/xxx
git switch main
git branch -d feat/xxx
git push origin --delete feat/xxx

# 提交
git add .
git commit -m "feat: ..."
git commit --amend

# 历史与差异
git log --oneline --graph
git diff
git show

# 回退
git reset --soft HEAD~1
git revert <sha>

# 暂存
git stash push -m "WIP"
git stash pop
```

---

> 建议：每次开始工作前先 `git pull --ff-only origin main`，  
> 每个功能/修复用单独分支，合并后删除分支，保持仓库干净。

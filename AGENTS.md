# Repository Agent Guidelines

## 铁律：GitHub 账号与 Remote 配置绑定规则 (GitHub Account & Remote Alignment Rule)

**必须严格遵守以下规则进行 Git 操作：**

1. **读取项目配置**：Agent 在当前项目中执行任何与 Git / GitHub 相关的操作（如创建分支、提交 commit、push 代码、创建 PR、调用 GitHub CLI 等）之前，**必须首先显式读取当前项目的 Git 远程配置** `remote.origin.url`：
   ```bash
   git config remote.origin.url
   ```
2. **解析目标账号**：从返回的 `remote.origin.url`（例如 `https://forchain@github.com/forchain/skills`）中准确解析项目所绑定的 GitHub 账号（例如 `forchain`）。
3. **隔离全局账号状态**：**严禁**盲目使用当前系统全局激活或登录的 GitHub 账号/凭证来推断本项目的提交与分支身份。全局激活的账号可能是为其他项目使用的，而不同项目使用的 GitHub 账号各不相同。
4. **绑定身份执行**：所有的提交 Author/Committer 以及 GitHub CLI / API 操作，必须严格与 `remote.origin.url` 解析出来的账号对齐。

## 铁律：分支命名规则 (Branch Naming Rule)

**创建或更新 Pull Request 之前，分支名必须符合 `feat/<描述>` 或 `fix/<描述>` 格式，且 `<描述>` 必须概括本次提交的实际内容。**

1. **校验**：执行任何 PR 操作之前，先运行 `git branch --show-current` 校验分支名。
2. **改名**：分支名不符合要求时，先重命名分支再操作 PR。本地用 `git branch -m <old> <new>`；远程用 GitHub 分支重命名接口，该接口会关闭已开的 PR，需从新分支重建 PR 并在旧 PR 注明接替关系。
3. **相关**：`<描述>` 概括本次提交改了什么，让只看分支名的人就能判断变更范围，例如 `feat/optimize-agent-writing`、`fix/validate-skill-name`。
4. **具体**：`<描述>` 使用小写字母、数字和连字符；无意义或随机命名不合规，例如 `feat/x`、`feat/update`、`feat/test`、`fix/1`。

不符合格式的示例：`wobbegong`、`feat-optimize-agent-writing`、`feature/login`、`hotfix/login`。

## Agent skills

### Issue tracker

Issues and specs live in GitHub Issues on `forchain/skills`; use the `gh` CLI. See `docs/agents/issue-tracker.md`.

### Triage labels

Use the default five-label vocabulary (`needs-triage`, `needs-info`, `ready-for-agent`, `ready-for-human`, `wontfix`). See `docs/agents/triage-labels.md`.

### Domain docs

This is a single-context repository: one root `GLOSSARY.md` plus `docs/adr/`. See `docs/agents/domain.md`.

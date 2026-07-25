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

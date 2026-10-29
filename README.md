# OpenFDE 案例访谈

帮助 FDE 把实际交付经历整理成可用于认证评审与合作匹配的案例。Agent 先阅读获授权的已有资料，再按回答逐轮追问，补齐业务流程、个人贡献、交付阶段、成效与商务口径，保留多个相关案例。

已有材料能回答的内容直接复用。每轮通常问 2–4 个相关问题，不要求受访者填写整份问卷或重新制作一套材料。未知、拒绝披露与尚未询问分别记录；关键冲突经过追问后仍无法消解时，交给人工核验。

## 安装

使用现有 Skills CLI 从 GitHub 安装到 Codex 用户范围：

```sh
npx -y skills add Alan-Youngzhe/OpenFDE-case-interviewer --skill openfde-case-interviewer -a codex -g -y
```

安装器需要 Node.js 22.20 或更高版本。Skill 中的本地覆盖检查脚本使用 Python 3 标准库；连接 OpenFDE 官网时使用官网提供的 CLI，建议 Node.js 24。安装 Skill 不需要 OpenFDE 登录，上传案例时再由本人登录授权。

## 开始访谈

安装后，在 Codex 中输入：

```text
使用 $openfde-case-interviewer 帮我整理案例。先阅读我授权的资料，再逐轮访谈我，问清缺项和冲突，整理全部相关案例。上传前让我确认正文和附件。
```

官网「复制到 Codex」按钮可使用以下完整指令：

```text
请执行 npx -y skills add Alan-Youngzhe/OpenFDE-case-interviewer --skill openfde-case-interviewer -a codex -g -y 安装 OpenFDE 案例访谈 Skill。安装后读取该 Skill，开始访谈我，结合我授权的资料逐轮追问，整理全部相关案例，上传前让我确认正文和附件。
```

如果安装后未显示该 Skill，重新打开 Codex 再使用。

## 访谈内容与交付

[查看交互式问题树](docs/question-tree.html)（下载后用浏览器打开），或直接阅读[问题库](references/question-bank.md)。

- 100 条可复用问题模板，覆盖 16 组访谈分支；根据缺口选用，不逐题机械询问。
- 对每个案例检查 14 类主题，并映射已有案例库的 26 个字段。
- 保存会话进度、问题回答、来源与冲突，支持暂停后继续。
- 整理案例卡、当前可售范围及合作条件、附件与使用权限清单。
- 为后续约 15 分钟人工认证访谈提炼关键决策、证据核验与未消解冲突。

有标品时可进一步梳理典型任务、演示脚本与宣传素材。录屏、剪辑和视频生成依赖使用者环境中的相应工具，属于可选分支；没有现成工具时交付脚本和步骤。

## 官网提交

官网入口为 [OpenFDE 实践案例](https://openfde.net/zh/account/solutions)。接入说明见 [website.md](references/website.md)，实际字段以官网 CLI 返回的 schema 为准。

Agent 在本地整理案例，展示拟上传正文和附件清单，经本人确认后上传。读取资料、上传私有草稿、提交认证评审和公开传播分别处理。完整合同和对话记录不是必交材料，可使用必要的脱敏节选。

案例提交不会自动提交认证申请、授予认证或公开发布案例。

## 文件结构

```text
SKILL.md                         访谈工作流程与边界
agents/openai.yaml               Codex 显示信息与示例指令
references/question-bank.md      问题库
references/coverage.md           字段映射、完成标准与会话格式
references/follow-up-examples.md 多轮追问示例
references/website.md            官网授权、预览与提交说明
scripts/interview_status.py      本地覆盖检查
docs/question-tree.html          可交互的问题树与模拟追问
```

## 本地覆盖检查

按照 [会话格式](references/coverage.md) 保存访谈记录后运行：

```sh
python3 scripts/interview_status.py /path/to/openfde-interview/session.json
```

退出码 0 表示覆盖记录可供用户确认，1 表示仍有待访项或会话已暂停/提前结束，2 表示记录结构存在问题。脚本只检查遗漏和状态，不能判断事实真假、认证资格或上传权限。

当前已完成 Skill 结构校验和覆盖检查脚本的 12 项状态检查，问题树的 18 条模拟路径已验证；尚未完成真实 FDE 的全流程试访。官网的复制入口与本仓库安装命令需要在官网端另行配置。

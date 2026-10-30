# OpenFDE 官网接入

访谈本身不依赖网站登录。需要同步既有案例或提交时再接入，尽量把用户操作集中到登录授权和一次具体内容确认。下面是官网现有 CLI 协议的操作参考，运行时以官方 CLI 的 help/schema 和实际回执为准；本 Skill 不包含上传凭证、服务器或托管下载地址。

## 连接本人账号

官网入口：`https://openfde.net/zh/account/solutions`。CLI 仅依赖 Node.js 内置模块，建议 Node.js 24。从官方域名下载到本地工作目录，检查文件和帮助后使用：

```sh
curl --fail --location https://openfde.net/downloads/openfde.mjs --output openfde.mjs
node ./openfde.mjs help --json
node ./openfde.mjs login --base-url https://openfde.net --scope solutions --no-wait --json
```

把返回的 `verificationUrl` 与 `userCode` 展示给本人，由本人在官网授权。然后：

```sh
node ./openfde.mjs login --complete --json
node ./openfde.mjs whoami --json
node ./openfde.mjs solution-schema --json
node ./openfde.mjs solutions --json
```

只申请 `solutions` 权限，不为采集顺便申请全部工作台权限。已登录且范围足够可复用会话；凭证由 CLI 私有存储，不复制到文档、案例、命令参数或 Skill。`AUTHORIZATION_PENDING`/退出码 6 表示本人尚未授权，等待其完成后再重试，不能替本人同意。

## 本地整理与确认

读取账号中相关旧案例后，按本次访谈补充；保留稳定的本地案例 ID 与网站 ID 对照，避免重复新建。生成官网模板并按运行时字段限制填入：

```sh
node ./openfde.mjs solution-template --output ./solution-template.json
node ./openfde.mjs solution-preview --data-file ./solution-template.json --output ./preview.html
```

字段映射见 coverage.md。超出主卡字段的信息放经确认的补充正文/附件；不能因为限制截断关键口径。不同客户保留为不同案例，超出网站容量时留在本地待同步，不能默默丢弃。

在任何草稿或附件离开本机前，展示这一批的正文预览与附件清单：对应案例、文件名、支持内容、脱敏方式、用途和提交目标。明确哪些只本地保留、哪些上传为私有草稿、哪些提交评审。本人可一次确认整批，确认后无需逐文件反复请求。登录授权不是上传确认，新增材料/用途需补充确认。

完整会话检查点通常含私人线索和路径，不默认上传。合同优先使用本人有权提供的必要脱敏节选；原始材料可仅在本地作为整理线索。

## 写入与正式提交

以下是命令形态，执行前替换 ID、版本、文件路径、请求编号，并确认输入对应正确案例：

```sh
node ./openfde.mjs solution-upload --data-file ./solution.json --request-id REQUEST_UUID --json
node ./openfde.mjs solution SOLUTION_ID --output ./existing-solution.json
node ./openfde.mjs solution-update SOLUTION_ID --data-file ./existing-solution.json --version VERSION --request-id REQUEST_UUID --json
node ./openfde.mjs solution-attach SOLUTION_ID --file ./approved-evidence.pdf --request-id REQUEST_UUID --json
```

新建、更新、附件和正式提交各用自己的稳定请求编号。更新保留导出的 ID/版本，只修改本次确认的字段。附件写入后读取服务器记录，核对本批清单中的每个文件 ID、名称和实际字节数。使用正式 CLI 导出与本 Skill 的校验脚本：

```sh
node ./openfde.mjs solution SOLUTION_ID --output ./draft-receipt.json
python3 /path/to/openfde-case-interviewer/scripts/verify_submission.py ./attachment-manifest.json ./draft-receipt.json
```

本人确认提交评审后，使用核对过的当前版本执行 `solution-submit`，再导出不同文件名的记录并核验正式提交快照：

```sh
node ./openfde.mjs solution-submit SOLUTION_ID --version VERSION --confirm --request-id REQUEST_UUID --json
node ./openfde.mjs solution SOLUTION_ID --output ./submission-receipt.json
python3 /path/to/openfde-case-interviewer/scripts/verify_submission.py ./attachment-manifest.json ./submission-receipt.json --submitted
```

清单格式与无附件处理见 [材料采集](materials.md)。核验通过后，将结果摘要、官网案例 ID、正式提交版本和附件数量交给本人。核验失败时如实说明已完成到哪一步，先查服务器记录、按原请求编号恢复；不要把仅上传草稿说成已提交评审。

正式提交的 `--confirm` 只在本人已经确认该批材料真实、有权提供并按要求脱敏，且明确同意提交评审时使用。私有草稿只有本人可见；正式提交后评审可读提交快照，后续修改需再次提交才更新评审内容。案例提交不等于公开发布、认证申请提交或认证通过。

目前文档所述容量为每账号 50 个案例、每案例 100 个附件且合计 2 GiB、单文件 256 MiB；运行时 schema 若有变化以新值为准。视频过大时保留原件，在本人许可下提供适用压缩版或已有授权链接。

## 可恢复错误

- 版本冲突/退出码 4：读取最新记录，与本地改动合并；如正文或附件有实质变化，更新用户预览确认，再用新请求编号写入。不要自动取最新版本覆盖他人修改。
- 网络结果不明/退出码 5：保存原输入及请求编号，用完全相同输入重试，避免新建重复案例。复合上传若给出 `partialResult.solutionId`，保存它并沿用根请求编号恢复；不要把步骤编号当根编号。
- 未授权/退出码 3：检查本人身份和权限，必要时重新授权；不可切换其他账号规避。
- 连续不可恢复错误：保留本地案例和回执，说明哪一步完成、哪一步未完成，不宣称已提交。

官网复制一句话的入口可在 Skill 托管后指向公开 Skill 包或稳定安装源；仅在本机安装不意味着其他 FDE 已能一键获取。本 Skill 包不能把本机绝对路径当成公开下载地址。

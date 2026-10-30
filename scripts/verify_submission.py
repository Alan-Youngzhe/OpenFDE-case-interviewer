#!/usr/bin/env python3
"""Compare an approved attachment manifest with an official CLI server export."""
import argparse
import json
import sys


def verify(manifest, solution, submitted=False):
    problems = []
    if not isinstance(manifest, dict) or not isinstance(solution, dict):
        return {"ok": False, "problems": ["清单和服务器记录须为 JSON 对象"]}
    solution_id = manifest.get("solution_id")
    if not isinstance(solution_id, str) or not solution_id.strip() or solution.get("id") != solution_id:
        problems.append("官网案例 ID 不一致")
    expected = manifest.get("files")
    if not isinstance(expected, list):
        return {"ok": False, "problems": problems + ["files 须为列表"]}
    if not expected and (not isinstance(manifest.get("no_attachments_reason"), str) or not manifest["no_attachments_reason"].strip()):
        problems.append("没有附件时须记录本人不能提供的原因")
    target = solution
    if submitted:
        target = solution.get("submitted_data") or {}
        if (solution.get("status") != "submitted" or target.get("id") != solution_id
                or target.get("version") != solution.get("version")):
            problems.append("最新版本尚未形成正式提交快照")
    actual = target.get("files", [])
    if not isinstance(actual, list):
        return {"ok": False, "problems": problems + ["服务器 files 须为列表"]}
    actual = {f.get("id"): f for f in actual if isinstance(f, dict)}
    seen, verified = set(), []
    for item in expected:
        if not isinstance(item, dict):
            problems.append("附件清单条目须为对象")
            continue
        file_id, name, size = item.get("file_id"), item.get("name"), item.get("size")
        if (not isinstance(file_id, str) or not file_id.strip()
                or not isinstance(name, str) or not name.strip()
                or not isinstance(size, int) or isinstance(size, bool) or size <= 0):
            problems.append("每个获准附件须有上传回执 file_id、文件名和正数字节数")
            continue
        if file_id in seen:
            problems.append("附件清单存在重复 file_id")
            continue
        seen.add(file_id)
        record = actual.get(file_id)
        if not record or record.get("name") != name or record.get("size") != size:
            problems.append("服务器附件缺失或名称/大小不一致：" + name)
        else:
            verified.append({"file_id": file_id, "name": name, "size": size})
    return {"ok": not problems, "solution_id": solution_id,
            "stage": "submitted" if submitted else "draft",
            "version": target.get("version"), "verified_files": verified,
            "text_only": not actual, "problems": problems}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("manifest")
    parser.add_argument("server_export")
    parser.add_argument("--submitted", action="store_true")
    args = parser.parse_args()
    try:
        with open(args.manifest, encoding="utf-8") as f:
            manifest = json.load(f)
        with open(args.server_export, encoding="utf-8") as f:
            solution = json.load(f)
        result = verify(manifest, solution, args.submitted)
    except (OSError, ValueError) as error:
        print(json.dumps({"ok": False, "problems": [str(error)]}, ensure_ascii=False))
        return 2
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())

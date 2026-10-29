#!/usr/bin/env python3
"""Check interview coverage, not factual truth, consent, or certification."""

import argparse
import json
import sys


TOPICS = (
    "identity", "problem", "workflow", "solution", "contribution", "engineering",
    "stage", "duration", "commercial", "outcomes", "reuse", "materials",
    "publication", "current_offer",
)


def nonempty(value):
    return isinstance(value, str) and bool(value.strip())


def string_list(value):
    return isinstance(value, list) and bool(value) and all(nonempty(v) for v in value)


def inspect_session(session):
    errors, outstanding, review = [], [], []
    if not isinstance(session, dict):
        return {"errors": ["会话根节点必须是对象"], "ready_for_user_confirmation": False}
    cases = session.get("cases", [])
    questions = session.get("questions", [])
    sources = session.get("sources", [])
    if not isinstance(cases, list) or not cases:
        errors.append("cases 必须是非空列表")
        cases = []
    if not isinstance(questions, list):
        errors.append("questions 必须是列表")
        questions = []
    if not isinstance(sources, list):
        errors.append("sources 必须是列表")
        sources = []

    def index_records(records, label):
        result = {}
        for record in records:
            if not isinstance(record, dict) or not nonempty(record.get("id")):
                errors.append(f"{label} 中每条须有非空 id")
                continue
            key = record["id"]
            if key in result:
                errors.append(f"{label} 存在重复 id: {key}")
            else:
                result[key] = record
        return result

    case_map = index_records(cases, "cases")
    question_map = index_records(questions, "questions")
    source_map = index_records(sources, "sources")

    def valid_sources(refs, location):
        if not string_list(refs):
            errors.append(f"{location}: 缺少 source_refs")
            return False
        missing = [ref for ref in refs if ref not in source_map]
        if missing:
            errors.append(f"{location}: 来源不存在: {', '.join(missing)}")
        return not missing

    def has_answer(refs, case_id, topic, location):
        if not string_list(refs):
            errors.append(f"{location}: 未提供实际追问的 question_ids")
            return False
        valid = True
        for ref in refs:
            q = question_map.get(ref)
            if (not q or q.get("case_id") != case_id or q.get("topic") != topic
                    or q.get("status") != "answered" or not nonempty(q.get("answer"))):
                errors.append(f"{location}: {ref} 不是本案例本主题的已回答问题")
                valid = False
        return valid

    for source_id, source in source_map.items():
        if not nonempty(source.get("type")) or not nonempty(source.get("locator")):
            errors.append(f"来源 {source_id}: 须有 type 和可定位的 locator")

    for question_id, question in question_map.items():
        if question.get("case_id") not in case_map or question.get("topic") not in TOPICS:
            errors.append(f"问题 {question_id}: 案例或主题不存在")
        if not nonempty(question.get("question")):
            errors.append(f"问题 {question_id}: 缺少问题正文")
        status = question.get("status", "pending")
        if status == "pending":
            outstanding.append({"case_id": question.get("case_id"), "question_id": question_id,
                                "kind": "pending_question", "topic": question.get("topic")})
        elif status == "answered":
            if not nonempty(question.get("answer")):
                errors.append(f"问题 {question_id}: answered 但没有实际回答")
            valid_sources(question.get("source_refs"), f"问题 {question_id}")
        elif status == "withdrawn":
            if not nonempty(question.get("reason")):
                errors.append(f"问题 {question_id}: withdrawn 须说明原因")
        else:
            errors.append(f"问题 {question_id}: 无效状态 {status}")

    for case_id, case in case_map.items():
        if not nonempty(case.get("title")):
            errors.append(f"案例 {case_id}: 缺少 title")
        topics = case.get("topics", {})
        if not isinstance(topics, dict):
            errors.append(f"案例 {case_id}: topics 必须是对象")
            topics = {}
        for extra in set(topics) - set(TOPICS):
            errors.append(f"案例 {case_id}: 未知主题 {extra}")
        for topic in TOPICS:
            item = topics.get(topic, {"status": "unasked"})
            location = f"{case_id}/{topic}"
            if not isinstance(item, dict):
                errors.append(f"{location}: 主题记录必须是对象")
                continue
            status = item.get("status", "unasked")
            if status in ("unasked", "partial"):
                outstanding.append({"case_id": case_id, "topic": topic, "kind": status})
            elif status == "answered":
                if not nonempty(item.get("summary")):
                    errors.append(f"{location}: answered 须有具体 summary")
                valid_sources(item.get("source_refs"), location)
            elif status in ("unknown", "declined"):
                if not nonempty(item.get("reason")):
                    errors.append(f"{location}: {status} 须有 reason")
                has_answer(item.get("question_ids"), case_id, topic, location)
                review.append({"case_id": case_id, "topic": topic, "kind": status,
                               "reason": item.get("reason", "")})
            elif status == "not_applicable":
                if not nonempty(item.get("reason")):
                    errors.append(f"{location}: not_applicable 须有适用性原因")
            else:
                errors.append(f"{location}: 无效状态 {status}")

        conflicts = case.get("conflicts", [])
        if not isinstance(conflicts, list):
            errors.append(f"案例 {case_id}: conflicts 必须是列表")
            conflicts = []
        conflict_map = index_records(conflicts, f"{case_id}/conflicts")
        for conflict_id, conflict in conflict_map.items():
            location = f"{case_id}/conflict/{conflict_id}"
            topic = conflict.get("topic")
            if topic not in TOPICS:
                errors.append(f"{location}: 无效主题")
            claims = conflict.get("claims", [])
            if not isinstance(claims, list) or len(claims) < 2:
                errors.append(f"{location}: 须保留至少两条 claims")
                claims = []
            for claim in claims:
                if not isinstance(claim, dict) or not nonempty(claim.get("text")):
                    errors.append(f"{location}: claim 须有 text")
                else:
                    valid_sources(claim.get("source_refs"), location)
            status = conflict.get("status", "open")
            if status == "open":
                outstanding.append({"case_id": case_id, "conflict_id": conflict_id,
                                    "topic": topic, "kind": "open_conflict"})
            elif status == "resolved":
                if not nonempty(conflict.get("resolution")):
                    errors.append(f"{location}: resolved 须有 resolution")
                valid_sources(conflict.get("source_refs"), location)
            elif status in ("unknown", "declined"):
                if not nonempty(conflict.get("reason")):
                    errors.append(f"{location}: {status} 须有 reason")
                has_answer(conflict.get("question_ids"), case_id, topic, location)
                review.append({"case_id": case_id, "conflict_id": conflict_id,
                               "topic": topic, "kind": "unresolved_for_human",
                               "reason": conflict.get("reason", "")})
            else:
                errors.append(f"{location}: 无效状态 {status}")

    status = session.get("status", "active")
    if status not in ("active", "paused", "ended"):
        errors.append("会话 status 必须为 active/paused/ended")
    return {
        "case_count": len(case_map), "session_status": status,
        "errors": errors, "outstanding": outstanding, "human_review": review,
        "ready_for_user_confirmation": not errors and not outstanding and status == "active",
        "meaning": "仅检查覆盖记录，不核验事实、不授予认证、不构成上传许可",
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("session_file", help="本地访谈 session.json")
    args = parser.parse_args()
    try:
        with open(args.session_file, encoding="utf-8") as handle:
            report = inspect_session(json.load(handle))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        report = {"errors": [str(exc)], "ready_for_user_confirmation": False}
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 2 if report.get("errors") else 0 if report["ready_for_user_confirmation"] else 1


if __name__ == "__main__":
    sys.exit(main())

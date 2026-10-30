import copy
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from verify_submission import verify
from interview_status import inspect_session, TOPICS


class SubmissionTests(unittest.TestCase):
    def setUp(self):
        self.file = {"id": "file-1", "name": "result.png", "size": 100}
        self.manifest = {"solution_id": "case-1", "files": [
            {"file_id": "file-1", "name": "result.png", "size": 100}]}
        self.record = {"id": "case-1", "version": 3, "status": "submitted",
                       "files": [self.file], "submitted_data": {
                           "id": "case-1", "version": 3, "files": [self.file]}}

    def test_received_and_submitted_are_separate(self):
        self.record["submitted_data"]["files"] = []
        self.assertTrue(verify(self.manifest, self.record)["ok"])
        self.assertFalse(verify(self.manifest, self.record, True)["ok"])

    def test_complete_receipt(self):
        self.assertTrue(verify(self.manifest, self.record, True)["ok"])

    def test_wrong_case_or_size(self):
        wrong = copy.deepcopy(self.record)
        wrong["id"] = "another-case"
        self.assertFalse(verify(self.manifest, wrong)["ok"])
        wrong = copy.deepcopy(self.manifest)
        wrong["files"][0]["size"] = 101
        self.assertFalse(verify(wrong, self.record)["ok"])

    def test_unreceived_or_unsubmitted_materials(self):
        self.manifest["files"][0]["file_id"] = ""
        self.assertFalse(verify(self.manifest, self.record)["ok"])
        self.record["status"] = "draft"
        self.assertFalse(verify(self.manifest, self.record, True)["ok"])

    def test_text_only_requires_explicit_reason(self):
        manifest = {"solution_id": "case-1", "files": []}
        self.record["files"] = []
        self.assertFalse(verify(manifest, self.record)["ok"])
        manifest["no_attachments_reason"] = "本人明确没有可提供材料"
        result = verify(manifest, self.record)
        self.assertTrue(result["ok"])
        self.assertTrue(result["text_only"])

    def test_duplicate_receipt_rejected(self):
        self.manifest["files"] *= 2
        self.assertFalse(verify(self.manifest, self.record)["ok"])


class CollectionTests(unittest.TestCase):
    def setUp(self):
        self.session = {"status": "active", "sources": [
            {"id": "reply:1", "type": "provider_statement", "locator": "第1轮"}],
            "questions": [], "cases": [{"id": "case-1", "title": "Case",
                "topics": {topic: {"status": "answered", "summary": "具体回答",
                                     "source_refs": ["reply:1"]} for topic in TOPICS}}]}
        self.case = self.session["cases"][0]

    def test_text_inventory_does_not_mean_files_received(self):
        self.assertFalse(inspect_session(self.session)["ready_for_user_confirmation"])

    def test_pending_files_remain_open(self):
        self.case["material_collection"] = {"status": "pending", "next_action": "等待截图"}
        self.assertFalse(inspect_session(self.session)["ready_for_user_confirmation"])

    def test_received_files_have_actual_metadata(self):
        self.case["material_collection"] = {"status": "received", "source_refs": ["reply:1"],
            "assets": [{"id": "asset-1", "name": "result.png", "local_path": "./result.png",
                "size": 100, "kind": "screenshot", "supports": "实际输出", "source_refs": ["reply:1"]}]}
        self.assertTrue(inspect_session(self.session)["ready_for_user_confirmation"])
        self.case["material_collection"]["assets"] = []
        self.assertFalse(inspect_session(self.session)["ready_for_user_confirmation"])

    def test_explicit_unavailable_does_not_block_interview(self):
        self.session["questions"] = [{"id": "m1", "case_id": "case-1", "topic": "materials",
            "question": "有什么已有材料可以提供？", "status": "answered",
            "answer": "受保密约束，不能提供文件。", "source_refs": ["reply:1"]}]
        self.case["material_collection"] = {"status": "declined", "reason": "保密约束",
            "question_ids": ["m1"], "source_refs": ["reply:1"]}
        self.assertTrue(inspect_session(self.session)["ready_for_user_confirmation"])


if __name__ == "__main__":
    unittest.main()

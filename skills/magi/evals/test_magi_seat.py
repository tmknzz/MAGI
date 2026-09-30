import importlib.util
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

path = Path(__file__).resolve().parents[1] / "scripts/magi-seat.py"
loader = importlib.util.spec_from_file_location("magi_seat", path)
magi = importlib.util.module_from_spec(loader)
loader.loader.exec_module(magi)


class Seats(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.env = patch.dict(os.environ, {"MAGI_CONFIG_DIR": str(self.root)}, clear=True)
        self.env.start()
        self.preflight = patch.object(magi, "preflight_pi")
        self.preflight.start()
        (self.root / "formations").mkdir()

    def tearDown(self):
        self.preflight.stop()
        self.env.stop()
        self.temp.cleanup()

    def formation(self, content):
        (self.root / "formations/local.conf").write_text(content)

    def test_default_and_partial(self):
        self.assertEqual([s["executor"] for s in magi.resolve().values()], ["primary"] * 3)
        self.formation("MAGI-M: pi local/org/Qwen3.8 high\n--\nanything here\n")
        result = magi.resolve("local")
        self.assertEqual(result["M"]["model"], "local/org/Qwen3.8")
        self.assertEqual(result["M"]["thinking"], "high")
        self.assertEqual(result["B"]["executor"], "primary")

    def test_three_distinct_and_priority(self):
        self.formation("M: pi local/Qwen off\nB: claude opus high\nC: codex gpt-6-astra low")
        os.environ["MAGI_FORMATION"] = "missing"
        with patch.object(magi, "vdgg_call", side_effect=AssertionError("must not call VDGG")):
            result = magi.resolve("local", "/not-used")
        self.assertEqual([x["executor"] for x in result.values()], ["pi", "claude", "codex"])

    def test_invalid_settings_fail(self):
        for content in ["M: primary high", "M: pi local/Qwen ultra", "M: primary\nM: codex", "X: codex", "M: codex $(touch /tmp/pwn)", "M: pi local/Qwen:high low", "M: pi Qwen high"]:
            with self.subTest(content=content):
                self.formation(content)
                with self.assertRaises(ValueError):
                    magi.resolve("local")
        with self.assertRaises(ValueError):
            magi.resolve("../../outside")
        with self.assertRaises(FileNotFoundError):
            magi.resolve("missing")

    def test_vdgg_assignments_preserve_contract(self):
        with patch.object(magi, "vdgg_call", side_effect=["inline\n", "fable5 high\n", "qwen\ncodex low\n"]):
            result = magi.resolve(vdgg_helper="/trusted/state.sh")
        self.assertEqual(result["M"]["executor"], "primary")
        self.assertEqual(result["C"]["assignment"], ["qwen", "codex low"])

    def test_pi_flags_and_model(self):
        argv = magi.argv_for(magi.spec("pi local/org/Qwen high"), self.root / "out")
        self.assertIn("--no-tools", argv)
        self.assertIn("--no-context-files", argv)
        self.assertIn("--no-extensions", argv)
        self.assertEqual(argv[argv.index("--provider") + 1], "local")
        self.assertEqual(argv[argv.index("--model") + 1], "org/Qwen")
        self.assertEqual(argv[-2:], ["--thinking", "high"])
        for value, flag in [("codex gpt-6-astra high", "-c"), ("claude opus medium", "--effort")]:
            self.assertIn(flag, magi.argv_for(magi.spec(value), self.root / "out"))

    def test_model_thinking_positional_order(self):
        self.assertEqual(magi.spec("codex minimal high")["model"], "minimal")
        self.assertEqual(magi.spec("codex minimal high")["thinking"], "high")
        self.assertEqual(magi.spec("claude high medium")["model"], "high")
        self.assertEqual(magi.spec("codex high")["thinking"], "high")

    def test_response_validation(self):
        for score in [0, 79, 80, 100]:
            self.assertEqual(magi.validate(f"SCORE: {score}\n詰め: 根拠あり\n提案: 具体案"), score)
        for reply in ["", "SCORE: 101\n詰め: x\n提案: y", "SCORE: 80\n詰め: \n提案: y", "SCORE: 80\n詰め: x\n提案: y\nextra"]:
            with self.assertRaises(ValueError):
                magi.validate(reply)
        self.assertIsNone(magi.validate("提案: 開幕案", opening=True))

    def test_no_primary_substitution(self):
        with patch.object(magi, "command_run", side_effect=AssertionError("do not launch")):
            with self.assertRaisesRegex(ValueError, "calling AI"):
                magi.run_seat("M", magi.spec("primary"), "案", self.root / "out")

    def test_personas_and_snapshot(self):
        for seat, name in magi.SEATS.items():
            prompt = magi.prepare(seat, "SAME CANDIDATE")
            self.assertIn(name, prompt)
            self.assertTrue(prompt.endswith("SAME CANDIDATE"))
            for other in set(magi.SEATS.values()) - {name}:
                # The common scoring rules may mention another seat, but its persona is absent.
                self.assertNotIn("### ▣ " + other, prompt)

    def test_run_records_raw_vote_and_no_stale_output(self):
        output = self.root / "out"
        reply = "SCORE: 79\n詰め: 不足\n提案: 改善案\n"
        with patch.object(magi, "command_run", return_value=reply):
            record = magi.run_seat("C", magi.spec("pi local/Qwen off"), "案", output)
        self.assertEqual(output.read_text(), reply)
        self.assertEqual(record["score"], 79)
        with self.assertRaisesRegex(ValueError, "already exists"):
            magi.run_seat("C", magi.spec("pi local/Qwen off"), "案", output)

    def test_invalid_vote_and_executor_failure_publish_nothing(self):
        for value in ["SCORE: 999", ValueError("failed")]:
            output = self.root / "failed"
            with patch.object(magi, "command_run", side_effect=value if isinstance(value, Exception) else None, return_value=value):
                with self.assertRaises(ValueError):
                    magi.run_seat("M", magi.spec("pi local/Qwen low"), "案", output)
            self.assertFalse(output.exists())
            self.assertFalse(output.with_name("failed.json").exists())

    def test_preflight_checks_model_and_thinking(self):
        self.preflight.stop()
        assignment = magi.spec("pi local/Qwen high")
        with patch.object(magi, "command_run", return_value="provider model context max-out thinking images\nlocal Qwen 128K 4K yes no"):
            magi.preflight_pi(assignment, {}, self.root)
        for row in ["local Other 128K 4K yes no", "local Qwen 128K 4K no no"]:
            with patch.object(magi, "command_run", return_value="provider model context max-out thinking images\n" + row):
                with self.assertRaises(ValueError):
                    magi.preflight_pi(assignment, {}, self.root)

    def test_pi_columns_can_move_and_unknown_format_fails(self):
        self.preflight.stop()
        assignment = magi.spec("pi local/Qwen high")
        with patch.object(magi, "command_run", return_value="provider extra thinking model\nlocal value yes Qwen"):
            magi.preflight_pi(assignment, {}, self.root)
        with patch.object(magi, "command_run", return_value="unknown header"):
            with self.assertRaisesRegex(ValueError, "header"):
                magi.preflight_pi(assignment, {}, self.root)

    def test_vdgg_changed_assignment_refused(self):
        assignment = {"executor": "vdgg", "helper": "/trusted/helper", "assignment": ["codex high"]}
        with patch.object(magi, "vdgg_call", return_value="claude low") as call:
            with self.assertRaisesRegex(ValueError, "assignment changed"):
                magi.run_seat("M", assignment, "案", self.root / "out")
        self.assertEqual(call.call_count, 1)

    def test_real_timeout_and_nonzero(self):
        import sys
        with self.assertRaisesRegex(ValueError, "timed out"):
            magi.command_run([sys.executable, "-c", "import time; time.sleep(5)"], timeout=0.05)
        with self.assertRaisesRegex(ValueError, "exit 3"):
            magi.command_run([sys.executable, "-c", "raise SystemExit(3)"])


if __name__ == "__main__":
    unittest.main()

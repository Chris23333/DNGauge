"""离线单测：parse_metadata_file（不依赖 Qt，仅依赖 rawpy/PIL 导入）。"""

import json
import os
import tempfile
import unittest

import shotwell_compare as sc


SAMPLE = "PolandRawMFNRmeta_20260625_040450.txt"


def _write(tmpdir, name, content):
    p = os.path.join(tmpdir, name)
    with open(p, "w", encoding="utf-8") as fh:
        fh.write(content)
    return p


class ParseMetadataTests(unittest.TestCase):
    def setUp(self):
        self._dir = tempfile.mkdtemp()

    def test_multiframe_txt_takes_first_frame(self):
        # 多帧：第一帧 WbGain=2.06,1,1.51；第二帧不同，确保取首帧
        content = (
            "ID:0\nNumOfFrames:6\nbayer_layout:3\nISO:13738\n"
            "WbGain:2.060547,1.000000,1.513672\nBlackLevel:256,256,256,256\n"
            "ImageSize(width: 4096, height: 3072, stride: 8192)\n"
            "Optical Flow:  ColsxRowsxChannel(44x32x2)\n"
            "0.0 0.0 0.0\n"
            "ID:1\nbayer_layout:0\nWbGain:1.0,1.0,1.0\nBlackLevel:0,0,0,0\n"
        )
        p = _write(self._dir, "a.txt", content)
        d = sc.parse_metadata_file(p)
        self.assertIsNotNone(d)
        self.assertEqual(d["wb"], (2.060547, 1.0, 1.513672))
        self.assertEqual(d["black"], 256)
        self.assertEqual(d["black_all"], (256, 256, 256, 256))
        self.assertEqual(d["bayer_layout"], 3)

    def test_singleframe_txt_without_id(self):
        content = "bayer_layout:1\nWbGain:1.5,1.0,1.2\nBlackLevel:100,100,100,100\n"
        p = _write(self._dir, "b.txt", content)
        d = sc.parse_metadata_file(p)
        self.assertEqual(d["wb"], (1.5, 1.0, 1.2))
        self.assertEqual(d["black"], 100)
        self.assertEqual(d["bayer_layout"], 1)

    def test_json_metadata(self):
        content = json.dumps({
            "WbGain": [2.0, 1.0, 1.5],
            "BlackLevel": [256, 256, 256, 256],
            "bayer_layout": 2,
        })
        p = _write(self._dir, "c.json", content)
        d = sc.parse_metadata_file(p)
        self.assertEqual(d["wb"], (2.0, 1.0, 1.5))
        self.assertEqual(d["black"], 256)
        self.assertEqual(d["bayer_layout"], 2)

    def test_json_case_insensitive_keys(self):
        content = json.dumps({"wbgain": [1.1, 1.2, 1.3], "blacklevel": [10], "BAYER_LAYOUT": 0})
        p = _write(self._dir, "d.json", content)
        d = sc.parse_metadata_file(p)
        self.assertEqual(d["wb"], (1.1, 1.2, 1.3))
        self.assertEqual(d["black"], 10)
        self.assertEqual(d["bayer_layout"], 0)

    def test_missing_fields_do_not_block(self):
        # 只有 WbGain
        p = _write(self._dir, "e.json", json.dumps({"WbGain": [1.0, 1.0, 1.0]}))
        d = sc.parse_metadata_file(p)
        self.assertEqual(d["wb"], (1.0, 1.0, 1.0))
        self.assertIsNone(d["black"])
        self.assertIsNone(d["bayer_layout"])

    def test_bayer_out_of_range_kept_as_int(self):
        # 解析层只负责取值；越界判定在 panel 层。这里验证值原样返回。
        p = _write(self._dir, "f.txt", "ID:0\nbayer_layout:7\nWbGain:1,1,1\n")
        d = sc.parse_metadata_file(p)
        self.assertEqual(d["bayer_layout"], 7)

    def test_no_fields_returns_none(self):
        p = _write(self._dir, "g.txt", "hello world\nnothing useful here\n")
        self.assertIsNone(sc.parse_metadata_file(p))

    def test_unreadable_file_returns_none(self):
        p = os.path.join(self._dir, "missing.txt")
        self.assertIsNone(sc.parse_metadata_file(p))

    def test_unknown_extension_returns_none(self):
        p = _write(self._dir, "h.csv", "WbGain:1,1,1\n")
        self.assertIsNone(sc.parse_metadata_file(p))

    def test_blacklevel_unequal_channels(self):
        p = _write(self._dir, "i.txt", "ID:0\nBlackLevel:256,260,255,258\nWbGain:1,1,1\n")
        d = sc.parse_metadata_file(p)
        self.assertEqual(d["black"], 256)
        self.assertEqual(d["black_all"], (256, 260, 255, 258))

    def test_real_sample_file(self):
        # 样例文件（若存在）第一帧应为 WbGain 2.06/1/1.51, BlackLevel 256, bayer_layout 3
        here = os.path.dirname(os.path.abspath(__file__))
        sample = os.path.join(os.path.dirname(here), SAMPLE)
        if not os.path.exists(sample):
            self.skipTest(f"样例文件不存在: {sample}")
        d = sc.parse_metadata_file(sample)
        self.assertIsNotNone(d)
        self.assertEqual(d["wb"], (2.060547, 1.0, 1.513672))
        self.assertEqual(d["black"], 256)
        self.assertEqual(d["bayer_layout"], 3)


if __name__ == "__main__":
    unittest.main()

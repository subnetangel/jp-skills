# SPDX-License-Identifier: MIT
"""Functional checks for a real exported reel and a mismatched fixture."""
import json, pathlib, subprocess, sys, tempfile, unittest

SCRIPT = pathlib.Path(__file__).parent / 'reel_qa.py'

class ReelQA(unittest.TestCase):
    def fixture(self, target, size, audio=True):
        args = ['ffmpeg', '-v', 'error', '-nostdin', '-f', 'lavfi', '-i', f'testsrc2=s={size}:r=30']
        if audio:
            args += ['-f', 'lavfi', '-i', 'sine=frequency=440:sample_rate=48000', '-c:a', 'aac', '-ac', '2']
        subprocess.run(args + ['-t', '1', '-c:v', 'libx264', '-pix_fmt', 'yuv420p', '-movflags', '+faststart', str(target)], check=True)

    def audit(self, root, path, *extra):
        return subprocess.run([sys.executable, str(SCRIPT), '--root', str(root), *extra, str(path)], text=True, capture_output=True)

    def test_good_portrait_export(self):
        with tempfile.TemporaryDirectory() as d:
            root = pathlib.Path(d)
            f = root / 'good.mp4'
            self.fixture(f, '1080x1920')
            r = self.audit(root, f)
            self.assertEqual(r.returncode, 0, r.stderr + r.stdout)
            self.assertEqual(json.loads(r.stdout)['dimensions'], [1080, 1920])

    def test_bad_orientation_and_missing_audio(self):
        with tempfile.TemporaryDirectory() as d:
            root = pathlib.Path(d)
            f = root / 'bad.mp4'
            self.fixture(f, '1920x1080', False)
            r = self.audit(root, f)
            self.assertEqual(r.returncode, 1, r.stderr + r.stdout)
            report = json.loads(r.stdout)
            self.assertIn('dimensions', report['failed'])
            self.assertIn('audio_codec', report['failed'])

    def test_file_outside_or_symlink_is_refused(self):
        with tempfile.TemporaryDirectory() as d:
            root = pathlib.Path(d) / 'out'
            root.mkdir()
            source = root.parent / 'outside.mp4'
            self.fixture(source, '360x640')
            link = root / 'alias.mp4'
            link.symlink_to(source)
            self.assertEqual(self.audit(root, source).returncode, 2)
            self.assertEqual(self.audit(root, link).returncode, 2)

    def test_corrupt_mp4_is_not_a_pass(self):
        with tempfile.TemporaryDirectory() as d:
            root = pathlib.Path(d)
            f = root / 'fake.mp4'
            f.write_bytes(b'this is not a video')
            self.assertEqual(self.audit(root, f).returncode, 2)

if __name__ == '__main__':
    unittest.main()

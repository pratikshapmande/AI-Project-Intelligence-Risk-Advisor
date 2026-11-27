import unittest
from app.ingestion import extract_document, chunk_text

class IngestionTests(unittest.TestCase):
    def test_txt_extraction(self):
        result = extract_document("sample.txt", b"Project deadline is Friday.")
        self.assertEqual(result["file_type"], "txt")
        self.assertIn("Friday", result["text"])

    def test_csv_extraction(self):
        result = extract_document("tasks.csv", b"task,status\nPlan,Open\nBuild,In progress\n")
        self.assertIn("Plan", result["text"])
        self.assertEqual(result["metadata"]["row_count"], 2)

    def test_empty_file_rejected(self):
        with self.assertRaises(ValueError):
            extract_document("empty.txt", b"")

    def test_unsupported_extension_rejected(self):
        with self.assertRaises(ValueError):
            extract_document("script.exe", b"no")

    def test_chunk_overlap_and_content(self):
        text = " ".join(["project"] * 300)
        chunks = chunk_text(text, chunk_size=200, overlap=30)
        self.assertGreater(len(chunks), 1)
        self.assertTrue(all(chunks))

if __name__ == "__main__":
    unittest.main()

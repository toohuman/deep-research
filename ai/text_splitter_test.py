#!/usr/bin/env python3
import unittest
from text_splitter import split_text

class TextSplitterTest(unittest.TestCase):
    def test_split_text_default(self):
        text = "abcdefghijklmnopqrstuvwxyz"
        # Expecting chunks of 5 characters each.
        expected = ["abcde", "fghij", "klmno", "pqrst", "uvwxy", "z"]
        self.assertEqual(split_text(text, 5), expected)

    def test_split_text_empty(self):
        self.assertEqual(split_text("", 10), [])

    def test_split_text_chunk_size_large(self):
        text = "short text"
        self.assertEqual(split_text(text, 100), [text])

if __name__ == '__main__':
    unittest.main()

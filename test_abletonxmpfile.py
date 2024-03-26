import unittest
from datetime import datetime
from lxml import etree
from tempfile import NamedTemporaryFile
import os

from abletonxmpfile import AbletonXMPFile


class TestAbletonXMPFile(unittest.TestCase):
    def setUp(self):

        # copy test.xml to a temp file
        with open("test.xmp", "r") as file:
            xml = file.read()
        with NamedTemporaryFile(delete=True) as temp_file:
            temp_file.write(xml.encode())
            self.file_path = temp_file.name

        self.xmp_file = AbletonXMPFile(self.file_path)

    def test_init_with_existing_file(self):
        # Test that the class initializes correctly with an existing file
        self.assertFalse(self.xmp_file.is_changed)
        self.assertIsNotNone(self.xmp_file.root)

    def test_init_with_non_existing_file(self):
        # Test that the class initializes correctly with a non-existing file
        non_existing_file_path = "non_existing_file.xmp"
        xmp_file = AbletonXMPFile(non_existing_file_path)
        self.assertEqual(xmp_file.file_path, non_existing_file_path)
        self.assertFalse(xmp_file.is_changed)
        self.assertIsNotNone(xmp_file.root)

    def test_add_keyword(self):
        # Test adding a keyword to an existing item
        file_path = "test_file.wav"
        keyword = "music"
        self.xmp_file.add_keyword(file_path, keyword)
        item = self.xmp_file.root.xpath(
            f"//ablFR:items/rdf:Bag/rdf:li[ablFR:filePath='{file_path}']",
            namespaces=self.xmp_file.nsmap,
        )[0]
        keywords = item.xpath(
            "ablFR:keywords/rdf:Bag/rdf:li",
            namespaces=self.xmp_file.nsmap,
        )
        self.assertEqual(len(keywords), 1)
        self.assertEqual(keywords[0].text, keyword)
        self.assertTrue(self.xmp_file.is_changed)

    def test_add_same_keyword_twice(self):
        # Test adding the same keyword twice to an existing item
        file_path = "test_file '1>.wav"
        keyword = "music"
        self.xmp_file.add_keyword(file_path, keyword)
        self.xmp_file.add_keyword(file_path, keyword)
        items = self.xmp_file.root.xpath(
            f"//ablFR:items/rdf:Bag/rdf:li",
            namespaces=self.xmp_file.nsmap,
        )
        # assert that exactly one of the items has the same file path
        items = [
            item
            for item in items
            if item.xpath("ablFR:filePath", namespaces=self.xmp_file.nsmap)[0].text
            == file_path
        ]
        self.assertEqual(len(items), 1)

        keywords = items[0].xpath(
            "ablFR:keywords/rdf:Bag/rdf:li",
            namespaces=self.xmp_file.nsmap,
        )
        self.assertEqual(len(keywords), 1)
        self.assertEqual(keywords[0].text, keyword)
        self.assertTrue(self.xmp_file.is_changed)

    def test_add_keyword_to_new_item(self):
        # Test adding a keyword to a new item
        file_path = "new_file.wav"
        keyword = "sound"
        self.xmp_file.add_keyword(file_path, keyword)
        item = self.xmp_file.root.xpath(
            f"//ablFR:items/rdf:Bag/rdf:li[ablFR:filePath='{file_path}']",
            namespaces=self.xmp_file.nsmap,
        )[0]
        keywords = item.xpath(
            "ablFR:keywords/rdf:Bag/rdf:li",
            namespaces=self.xmp_file.nsmap,
        )
        self.assertEqual(len(keywords), 1)
        self.assertEqual(keywords[0].text, keyword)
        self.assertTrue(self.xmp_file.is_changed)

    def test_dump(self):
        # Test dumping the XML content
        xml = self.xmp_file.dump()
        self.assertIsInstance(xml, str)
        self.assertIn("<x:xmpmeta", xml)
        self.assertIn("<ablFR:items>", xml)
        self.assertIn("<xmp:MetadataDate>", xml)

    def test_save_if_changed(self):
        # Test saving the XML content to a file
        xml = self.xmp_file.dump()
        with NamedTemporaryFile(delete=False) as temp_file:
            temp_file.write(xml.encode())
            temp_file_path = temp_file.name

        self.xmp_file.save_if_changed(temp_file_path)
        self.assertFalse(self.xmp_file.is_changed)
        with open(temp_file_path, "r") as file:
            saved_xml = file.read()
        self.assertEqual(xml, saved_xml)


if __name__ == "__main__":
    unittest.main()

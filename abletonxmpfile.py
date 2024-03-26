from lxml import etree
from datetime import datetime
from xml.sax.saxutils import quoteattr, escape
import os


class AbletonXMPFile:
    def __init__(self, file_path=None):
        self.file_path = file_path
        self.is_changed = False
        self.nsmap = {
            "ablFR": "https://ns.ableton.com/xmp/fs-resources/1.0/",
            "rdf": "http://www.w3.org/1999/02/22-rdf-syntax-ns#",
        }
        self.parser = etree.XMLParser(remove_blank_text=True)
        try:
            with open(file_path, "r", encoding="utf-8") as file:
                self.root = etree.parse(file, self.parser).getroot()
        except FileNotFoundError:
            current_datetime = datetime.now().strftime("%Y-%m-%dT%H:%M:%S%z")
            template = f"""
                <x:xmpmeta xmlns:x="adobe:ns:meta/" x:xmptk="XMP Core 5.6.0">
                <rdf:RDF xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#">
                    <rdf:Description rdf:about=""
                            xmlns:dc="http://purl.org/dc/elements/1.1/"
                            xmlns:ablFR="https://ns.ableton.com/xmp/fs-resources/1.0/"
                            xmlns:xmp="http://ns.adobe.com/xap/1.0/">
                        <dc:format>application/vnd.ableton.folder</dc:format>
                        <ablFR:resource>folder</ablFR:resource>
                        <ablFR:platform>mac</ablFR:platform>
                        <ablFR:items>
                            <rdf:Bag>
                            
                            </rdf:Bag>
                        </ablFR:items>
                        <xmp:CreatorTool>Updated by Ableton Index 12.0</xmp:CreatorTool>
                        <xmp:CreateDate>{current_datetime}</xmp:CreateDate>
                        <xmp:MetadataDate>{current_datetime}</xmp:MetadataDate>
                    </rdf:Description>
                </rdf:RDF>
                </x:xmpmeta>
                """
            self.root = etree.XML(template, self.parser)

    def add_tag(self, file_path, keyword):
        added = False
        item_template = f"""
        <rdf:li rdf:parseType="Resource" 
                xmlns:ablFR="https://ns.ableton.com/xmp/fs-resources/1.0/"
                xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#">
            <ablFR:filePath>{escape(file_path)}</ablFR:filePath>
            <ablFR:keywords>
                <rdf:Bag>
                </rdf:Bag>
            </ablFR:keywords>
        </rdf:li>
        """

        items = self.root.xpath(
            f"//ablFR:items/rdf:Bag/rdf:li",
            namespaces=self.nsmap,
        )
        # collect existing filepaths
        existing_filepaths = [
            item.xpath("ablFR:filePath", namespaces=self.nsmap)[0].text
            for item in items
        ]
        # check if the file path already exists
        if file_path in existing_filepaths:
            item = items[existing_filepaths.index(file_path)]
        else:
            item = etree.XML(item_template, self.parser)
            self.root.xpath(
                "//ablFR:items/rdf:Bag",
                namespaces=self.nsmap,
            )[
                0
            ].append(item)
            added = True

        existing_keywords = item.xpath(
            "ablFR:keywords/rdf:Bag/rdf:li",
            namespaces=self.nsmap,
        )
        existing_keyword_values = [keyword.text for keyword in existing_keywords]
        if keyword not in existing_keyword_values:
            keywords_bag = item.xpath(
                "ablFR:keywords/rdf:Bag",
                namespaces=self.nsmap,
            )[0]
            new_keyword = etree.SubElement(
                keywords_bag, "{http://www.w3.org/1999/02/22-rdf-syntax-ns#}li"
            )
            new_keyword.text = keyword
            added = True

        if added:
            self.is_changed = True

        return added

    def dump(self):
        metadata_date = self.root.xpath(
            "//xmp:MetadataDate",
            namespaces={
                "xmp": "http://ns.adobe.com/xap/1.0/",
            },
        )
        if metadata_date is not None and len(metadata_date) > 0:
            metadata_date[0].text = datetime.now().strftime("%Y-%m-%dT%H:%M:%S%z")
        else:
            metadata_date = etree.Element("{http://ns.adobe.com/xap/1.0/}MetadataDate")
            metadata_date.text = datetime.now().strftime("%Y-%m-%dT%H:%M:%S%z")
            self.root.append(metadata_date)

        etree.indent(self.root)
        xml = etree.tostring(self.root, pretty_print=True).decode()

        return xml

    def save_if_changed(self, file_path=None):
        if not self.is_changed:
            return

        if not file_path:
            file_path = self.file_path

        xml = self.dump()

        folder_path = os.path.dirname(file_path)
        os.makedirs(folder_path, exist_ok=True)  # Ensure the folder exists

        with open(file_path, "w", encoding="utf-8") as file:
            file.write(xml)

        self.is_changed = False

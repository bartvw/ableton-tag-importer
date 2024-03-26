import sqlite3
from abletonxmpfile import AbletonXMPFile


class ADSRImporter:
    XMP_FILENAME = "dc66a3fa-0fe1-5352-91cf-3ec237e9ee90.xmp"

    KEY_MAP = {
        1: ("C", "Major"),
        3: ("C", "Minor"),
        4: ("C#", "Major"),
        6: ("C#", "Minor"),
        7: ("D", "Major"),
        9: ("D", "Minor"),
        10: ("D#", "Major"),
        12: ("D#", "Minor"),
        13: ("E", "Major"),
        15: ("E", "Minor"),
        16: ("F", "Major"),
        17: ("F", "Major"),  # Not sure why this is duplicated
        18: ("F", "Minor"),
        19: ("F#", "Major"),
        21: ("F#", "Minor"),
        22: ("G", "Major"),
        24: ("G", "Minor"),
        25: ("G#", "Major"),
        27: ("G#", "Minor"),
        28: ("A", "Major"),
        30: ("A", "Minor"),
        31: ("A#", "Major"),
        33: ("A#", "Minor"),
        34: ("B", "Major"),
        36: ("B", "Minor"),
    }

    def __init__(self, db_path, tag_map):
        self.xmpfilename = "dc66a3fa-0fe1-5352-91cf-3ec237e9ee90.xmp"
        self.conn = sqlite3.connect(db_path)
        self.cursor = self.conn.cursor()
        self.tag_map = tag_map

    def _fetch_tag_path(self, tag_id):
        self.cursor.execute(
            "SELECT name, parent_id,type FROM tags WHERE id = ?;", (tag_id,)
        )
        tag = self.cursor.fetchone()
        if tag[1] == -1:
            return tag[0]
        else:
            parent_path = self._fetch_tag_path(tag[1])
            return f"{parent_path}|{tag[0]}"

    def sync_directory(self, folder_path, dry_run=False, on_tag_added=None):
        unmapped_tags = set()
        num_tags_added = 0

        self.cursor.execute(
            "SELECT id,path FROM folders where path LIKE ?;", (f"{folder_path}%",)
        )
        items = self.cursor.fetchall()

        for folder in items:
            print(folder[1])
            xmp = AbletonXMPFile(f"{folder[1]}/Ableton Folder Info/{self.XMP_FILENAME}")

            self.cursor.execute(
                "SELECT id,name,loop FROM files WHERE folder_id = ?;", (folder[0],)
            )
            for file in self.cursor.fetchall():

                tags = set()
                self.cursor.execute(
                    "SELECT tag_id FROM file_tags WHERE file_id = ?;",
                    (file[0],),
                )
                for tag_name in [
                    self._fetch_tag_path(tag_id[0]) for tag_id in self.cursor.fetchall()
                ]:
                    if tag_name in self.tag_map and self.tag_map[tag_name]:
                        tag = self.tag_map[tag_name]
                        tags.add(tag)
                    else:
                        unmapped_tags.add(tag_name)

                if file[2] == 1:
                    tags.add("Type|Loop")
                else:
                    tags.add("Type|One Shot")

                # Get the key and tempo from the file
                self.cursor.execute(
                    "SELECT key FROM sample_meta WHERE id = ?;",
                    (file[0],),
                )
                # fetch the result
                result = self.cursor.fetchone()

                if result[0] != 0:
                    if result[0] not in self.KEY_MAP:
                        print(f"Unknown key: {result[0]}")
                    else:
                        root, mode = self.KEY_MAP[result[0]]
                        if root is not None and mode is not None:
                            tags.add(f"Key|{root}")
                            tags.add(f"Key|{mode}")

                for tag in tags:
                    if xmp.add_tag(file[1], tag):
                        num_tags_added += 1
                        if on_tag_added is not None:
                            on_tag_added(
                                {"file_path": f"{folder[1]}/{file[1]}", "tag": tag}
                            )

            if not dry_run:
                xmp.save_if_changed()

        self.cursor.close()
        self.conn.close()

        return (num_tags_added, list(unmapped_tags))

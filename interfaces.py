import bpy
import os
import json

class SCG_Cycler_Context_Interface:
    @property
    def cycler(self):
        return bpy.context.scene.scg_cycler_context

class SCG_Cycler_Collection_Wrapper:
    def __iter__(self):
        return self.children.__iter__()
    def __len__(self):
        return len(self.children)

class SCG_Cycler_Loads_From_JSON(SCG_Cycler_Collection_Wrapper):
    def search(self):
        self.children.clear()
        for path in self.paths:
            directory = os.fsencode(path.path)
            for file in os.listdir(directory):
                filename = os.fsdecode(file)
                if filename.endswith(".json"):
                    file_path = path.path + filename
                    f = open(file_path)
                    data = json.load(f)
                    f.close()
                    self.load(data)
        if self.data_text_name in bpy.data.texts:
            data_string = bpy.data.texts[self.data_text_name].as_string()
            data = json.loads(data_string)
            self.load(data)

    def load(self, json_data):
        if self.json_entries_name not in json_data: return
        entries = json_data[self.json_entries_name]
        for entry_name, entry_data in entries.items():
            if not entry_name in [entry.name for entry in self]:
                new_entry = self.children.add()
                new_entry.name = entry_name
                self.set_child_from_json_data(new_entry, entry_data)
            else:
                for child in self:
                    if child.name == entry_name:
                        self.set_child_from_json_data(child, entry_data)

    def create_text_data(self):
        data_text = bpy.data.texts.new(self.data_text_name)
        data_text.from_string(self.default_data_string)

    def add_to_data(self, name, json_data):
        if not self.data_text_name in bpy.data.texts:
            self.create_text_data()
        data_string = bpy.data.texts[self.data_text_name].as_string()
        data = json.loads(data_string)
        data[self.json_entries_name][name] = json_data
        bpy.data.texts[self.data_text_name].from_string(json.dumps(data, indent=3))

import bpy

class Panel_Factory:
    def __init__(self):
        self.panels = {}
    
    def register_new_panel(self, id, cls):
        self.panels[id]=cls
        from bpy.utils import register_class
        register_class(cls)

    def remove_panel(self, id):
        from bpy.utils import unregister_class
        unregister_class(self.panels[id])
        del self.panels[id]

    def remove_all_panels(self):
        from bpy.utils import unregister_class
        for panel_id, cls in self.panels.items():
            unregister_class(cls)
        del self.panels
        self.panels = {}

class Children_Have_Panels:
    panel_factory = Panel_Factory()

    @property
    def panel_ids(self):
        return [child.name for child in self]

    def add_panels(self):
        for panel_id in self.panel_ids:
            if panel_id not in self.panel_factory.panels:
                new_class = self.create_panel_class(panel_id=panel_id)
                self.panel_factory.register_new_panel(panel_id, new_class)

    def remove_panels(self):
        panels_to_remove = [panel_id for panel_id in self.panel_factory.panels if panel_id not in self.panel_ids]
        for panel_id in panels_to_remove:
            self.panel_factory.remove_panel(panel_id)

    def create_panel_class(self, **kwargs):
        return

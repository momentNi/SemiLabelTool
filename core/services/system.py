from core.configs.core import CORE

from core.dto.enums import ZoomMode


def set_dirty():
    print("set_dirty")
    # Even if we autosave the file, we keep the ability to undo
    # self.actions.undo.setEnabled(self.canvas.is_shape_restorable)

    # if self._config["auto_save"]:
    #     label_file = os.path.splitext(self.image_path)[0] + ".json"
    #     if self.output_dir:
    #         label_file_without_path = os.path.basename(label_file)
    #         label_file = self.output_dir + "/" + label_file_without_path
    #     self.save_labels(label_file)
    #     return
    # self.dirty = True
    # self.actions.save.setEnabled(True)
    # title = __appname__
    # if self.filename is not None:
    #     title = f"{title} - {self.filename}*"
    # self.setWindowTitle(title)


def set_clean():
    print("set_clean")
    # self.dirty = False
    # self.actions.save.setEnabled(False)
    # self.actions.union_selection.setEnabled(False)
    # self.actions.create_mode.setEnabled(True)
    # self.actions.create_rectangle_mode.setEnabled(True)
    # self.actions.create_rotation_mode.setEnabled(True)
    # self.actions.create_circle_mode.setEnabled(True)
    # self.actions.create_line_mode.setEnabled(True)
    # self.actions.create_point_mode.setEnabled(True)
    # self.actions.create_line_strip_mode.setEnabled(True)
    # title = __appname__
    # if self.filename is not None:
    #     title = f"{title} - {self.filename}"
    # self.setWindowTitle(title)
    #
    # if self.has_label_file():
    #     self.actions.delete_file.setEnabled(True)
    # else:
    #     self.actions.delete_file.setEnabled(False)


def reset_state():
    print("reset state")
    # self.label_list.clear()
    CORE.Variable.current_file_full_path = None
    CORE.Variable.label_file = None
    CORE.Object.canvas.reset_state()
    # CORE.Object.info_file_search.label_filter_combobox.combo_box.clear()


def on_item_description_change():
    print("on_item_description_change")
    description = CORE.Object.item_description.toPlainText()
    print(f"description: {description}")
    # if self.canvas.current is not None:
    #     self.canvas.current.description = description
    # elif self.canvas.editing() and len(self.canvas.selected_shapes) == 1:
    #     self.canvas.selected_shapes[0].description = description
    # else:
    #     self.other_data["image_description"] = description
    # self.set_dirty()


def set_zoom(value):
    print("set_zoom")
    # self.actions.fit_width.setChecked(False)
    # self.actions.fit_window.setChecked(False)
    CORE.Object.canvas.zoom_mode = ZoomMode.MANUAL_ZOOM
    # self.zoom_widget.setValue(value)
    CORE.Object.canvas.zoom_values[CORE.Variable.current_file_full_path] = (CORE.Object.canvas.zoom_mode, value)


def adjust_scale(initial=False):
    # value = self.scalers[ZoomMode.FIT_WINDOW if initial else CORE.Variable.zoom_mode]()
    # value = int(100 * value)
    # self.zoom_widget.setValue(value)
    CORE.Object.canvas.zoom_values[CORE.Variable.current_file_full_path] = (CORE.Object.canvas.zoom_mode, 100)

def get_mode():
    return "Editing"


def load_labels(shapes):
    s = []
    for shape in shapes:
        label = shape["label"]
        score = shape.get("score", None)
        points = shape["points"]
        shape_type = shape["shape_type"]
        flags = shape["flags"]
        group_id = shape["group_id"]
        description = shape.get("description", "")
        difficult = shape.get("difficult", False)
        attributes = shape.get("attributes", {})
        direction = shape.get("direction", 0)
        kie_linking = shape.get("kie_linking", [])
        other_data = shape["other_data"]

        if label in self.hidden_cls or not points:
            # skip point-empty shape
            continue

        shape = Shape(
            label=label,
            score=score,
            shape_type=shape_type,
            group_id=group_id,
            description=description,
            difficult=difficult,
            direction=direction,
            attributes=attributes,
            kie_linking=kie_linking,
        )
        for x, y in points:
            shape.add_point(QtCore.QPointF(x, y))
        shape.close()

        default_flags = {}
        if self.label_flags:
            for pattern, keys in self.label_flags.items():
                if re.match(pattern, label):
                    for key in keys:
                        default_flags[key] = False
        shape.flags = default_flags
        if flags:
            shape.flags.update(flags)
        shape.other_data = other_data

        s.append(shape)
    self.update_combo_box()
    self.load_shapes(s)

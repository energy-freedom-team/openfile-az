"""Fill AZ SOS fillable PDF directly by walking the AcroForm hierarchy and setting /V and /AS."""
import json
import sys
from pypdf import PdfReader, PdfWriter
from pypdf.generic import NameObject, TextStringObject, BooleanObject


def walk_fields(root, parent_name=""):
    """Yield (full_name, field_dict) for every leaf form field."""
    kids = root.get("/Kids")
    t = root.get("/T")
    name = parent_name
    if t is not None:
        name = f"{parent_name}.{t}" if parent_name else str(t)

    if kids:
        # Check if kids are fields or widget annotations
        has_field_kids = False
        for k in kids:
            kobj = k.get_object()
            if "/T" in kobj:
                has_field_kids = True
                break
        if has_field_kids:
            for k in kids:
                kobj = k.get_object()
                yield from walk_fields(kobj, name)
            return
    # Leaf field
    yield name, root


def set_text_field(field, value):
    field[NameObject("/V")] = TextStringObject(value)
    # Clear any existing appearance so the viewer regenerates
    if "/AP" in field:
        del field["/AP"]


def set_button_field(field, value):
    """value is the appearance-state name like '/On', '/Yes', '/Off'. Strip leading '/' for /AS."""
    val_name = value if value.startswith("/") else "/" + value
    state = NameObject(val_name)
    field[NameObject("/V")] = state

    kids = field.get("/Kids")
    if kids:
        for k in kids:
            kobj = k.get_object()
            if "/Subtype" in kobj and kobj["/Subtype"] == "/Widget":
                # Determine which /AS to set: /On state only if this widget's /AP/N contains val
                ap = kobj.get("/AP")
                if ap is not None:
                    n_states = set()
                    n = ap.get_object().get("/N")
                    if n is not None:
                        n_states = set(n.get_object().keys())
                    if val_name in n_states:
                        kobj[NameObject("/AS")] = state
                    else:
                        kobj[NameObject("/AS")] = NameObject("/Off")
                else:
                    kobj[NameObject("/AS")] = state
    else:
        # Widget merged with field
        kobj = field
        kobj[NameObject("/AS")] = state


def fill(input_pdf, fields_json, output_pdf):
    with open(fields_json) as f:
        target_fields = json.load(f)

    reader = PdfReader(input_pdf)
    writer = PdfWriter(clone_from=reader)

    # Walk the AcroForm tree
    root = writer._root_object["/AcroForm"]["/Fields"]
    field_index = {}
    for root_field_ref in root:
        rf = root_field_ref.get_object()
        for full_name, leaf in walk_fields(rf):
            field_index[full_name] = leaf

    for tf in target_fields:
        fid = tf["field_id"]
        val = tf["value"]
        field = field_index.get(fid)
        if field is None:
            print(f"SKIP: field not found: {fid!r}")
            continue
        ft = field.get("/FT")
        if ft == "/Tx":
            set_text_field(field, str(val))
        elif ft == "/Btn":
            set_button_field(field, str(val))
        else:
            # Try text as fallback
            set_text_field(field, str(val))

    # Force appearance regeneration
    writer._root_object["/AcroForm"][NameObject("/NeedAppearances")] = BooleanObject(True)

    with open(output_pdf, "wb") as f:
        writer.write(f)
    print(f"Wrote {output_pdf}")


if __name__ == "__main__":
    fill(sys.argv[1], sys.argv[2], sys.argv[3])

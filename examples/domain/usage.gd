extends SceneTree

func _initialize() -> void:
    var catalog = LinkMLCatalog.new()
    var item = LinkMLItem.new()
    assert(item.slot_kind == null and item.slot_labels == null)
    item.slot_id = "item:1"
    item.slot_kind = "tool"
    assert(item.slot_category == "tool")
    item.slot_quality = LinkMLQuality.VALUE__U03A9
    item.slot_labels = "portable"
    assert(item.slot_labels == "portable")
    item.slot_labels = ["portable", "shared"]
    item.slot_metadata = LinkMLMetadata.new()
    item.slot_metadata.slot_title = "Example"
    item.slot_metadata.linkml_extra_slots["Ω"] = "raw key"
    item.slot_metadata.linkml_extra_slots["counts"] = [1, 2]
    catalog.slot_items[item.slot_id] = item
    catalog.slot_featured = item.slot_id
    assert(catalog.slot_featured == "item:1")
    assert(catalog.slot_items["item:1"] is LinkMLItem)
    assert(catalog.slot_items["item:1"].slot_quality == "Ω")
    assert(item.slot_metadata.linkml_extra_slots["counts"] == [1, 2])
    assert(LinkMLMetadata.new().linkml_extra_slots.is_empty())
    assert(LinkMLCatalog.new().slot_items.is_empty())
    print("DOMAIN_MODEL_OK")
    quit()

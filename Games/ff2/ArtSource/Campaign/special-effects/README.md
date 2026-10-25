# Special effect source sheets

Two built-in image_gen source sheets cover eight families with four progressive frames each (32 frames). Every row is a family; columns are ignition, buildup, peak, dissipate, named frame01 through frame04. Target frame size is 32x32 with center pivot. Descriptors are in sheets.json, full requests are sibling .prompt.txt files, and generation-record.json includes original tool output paths and SHA256 hashes.

special-effects-a.png rows: bow-shot, boulders, earthquake, cyclone.

special-effects-b.png rows: tsunami, starfall, self-destruct, blaster.

Source tool previews were visually inspected: each row shows genuine shape/intensity progression and transparent gutters were requested. Center alpha samples are zero; top-left alpha is 1/255 in sheet A and 0 in sheet B. Final alpha-aware crop, normalized preview, and runtime approval belong to the campaign pipeline; source generation alone does not prove those checks.

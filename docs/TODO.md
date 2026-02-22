# TODO — Future Features

- ~~Project-wide labeling progress dashboard / summary statistics~~ (labeling dashboard added)
- ~~Inter-annotator agreement / review workflow~~ (multi-reviewer verification added)
- Multi-day file concatenation in viewer

## Verify: Datetime & Config Generalization

- [ ] Open yellowstone_cougars project — verify labels load with dates, plot titles show correctly
- [ ] Create a new label — verify it saves with full datetime (check JSON)
- [ ] Generate BEBE output — verify individual IDs extracted correctly via regex
- [ ] Check Y-axis uses config value ([-5, 5] from y_range)
- [ ] Create a new project — verify defaults work (no regex/y_range in config uses defaults)
- [ ] Open a legacy project with time-only labels — verify backward compatibility
- [ ] Drag-resize a label edge — verify updated time saves as full datetime

## Verify: Quick Wins & Undo/Redo

- [ ] Type rapidly in comments field — verify save only fires once after typing stops (check log)
- [ ] Generate output to a non-empty directory — verify confirmation dialog appears
- [ ] Click Cancel during output generation — verify it stops promptly
- [ ] Create a label, then Ctrl+Z — verify label is removed
- [ ] Ctrl+Y after undo — verify label is restored
- [ ] Delete a label, then Ctrl+Z — verify label reappears
- [ ] Drag a label edge, then Ctrl+Z — verify edge returns to original position
- [ ] Change a label's behavior, then Ctrl+Z — verify original behavior is restored
- [ ] Load a different file — verify undo stack is cleared (Ctrl+Z shows "Nothing to undo")

## Verify: Edit Input Settings

- [ ] Project > Edit Input Settings — verify dialog opens with current values
- [ ] Change frequency to 8 → Save → reopen dialog — verify value persisted
- [ ] Change y-range → Save → verify viewer Y-axis updates immediately
- [ ] Enter invalid regex (e.g. `(?P<broken`) → Save → verify error shown
- [ ] Clear plot title format → Save → verify error shown
- [ ] Set y-min >= y-max → Save → verify error shown

## Verify: Export/Import Labels CSV

- [ ] Open project with labels → Project > Export Labels to CSV → save file → open CSV → verify columns: file_id, file_path, behavior, start_time, end_time
- [ ] Verify exported times match project JSON format (full datetime or time-only)
- [ ] Export → delete some labels from project → Import CSV → choose Replace → verify labels restored
- [ ] Import into project with existing labels → verify conflict dialog appears (Yes/No/Cancel)
- [ ] Click Cancel on conflict dialog → verify entire import aborts
- [ ] Click No on conflict dialog → verify that file is skipped, others still import
- [ ] Import CSV referencing a non-existent file_id → verify it reports skipped files in summary
- [ ] Round-trip: export → import into same project → verify labels match exactly

## Verify: Multi-Reviewer Verification

- [ ] Load yellowstone_cougars.json — verify `user_verified: true` files show as verified by "default", tree colors correct
- [ ] Open a file → info pane shows reviewer checkboxes with aliases → only current user's is clickable
- [ ] Toggle verification → tree item changes color → reopen file → checkbox state persisted
- [ ] Filter by Verified/Partial/Unverified → correct files shown
- [ ] New project with no reviewers configured → single "Verified" checkbox shown, green on check
- [ ] Two reviewers configured, one verifies → tree shows yellow (partial), both verify → green

## Verify: Labeling Dashboard

- [ ] Open project → Project > Labeling Dashboard → dialog opens with correct stats
- [ ] Verify overview counts match manual count of files/labels in project browser
- [ ] Verify per-behavior table shows all configured behaviors with correct label counts and durations
- [ ] Verify per-reviewer table shows each reviewer with correct verified file counts
- [ ] Verify dialog works with no reviewers configured (reviewer section hidden)
- [ ] Verify dialog works with a project that has zero labels (all zeros, no crash)
- [ ] Close button dismisses the dialog

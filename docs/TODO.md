# TODO — Future Features

- ~~Project-wide labeling progress dashboard / summary statistics~~ (labeling dashboard added)
- ~~Inter-annotator agreement / review workflow~~ (multi-reviewer verification added)
- ~~Replace data_root_directory + reviewers with explicit users list~~ (user config refactor done)
- Multi-day file concatenation in viewer
- **Info pane clear/refresh on new project load** — when a new project is created or opened, the info pane should reset (clear file metadata, verification checkboxes, comments) so stale data from a previous session isn't visible.
- **Project browser drag-and-drop** — allow dragging a CSV entry from one subdirectory to another within the project browser tree; update the project config on drop.
- **Open file in viewer on add** — when a file is added to the project via right-click or menu, automatically open it in the viewer and zoom to fit all data (same as double-click behaviour).
- **Viewer zoom-to-fit on file open** — currently opening a file while zoomed all the way out shows nothing. Investigate whether the viewer needs a zoom reset on each new file opened. Consider whether tabs for multiple open files are feasible (memory tradeoff: each open file holds its full CSV in memory).

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

## Verify: Per-User Comments & Verification Threshold

- [ ] Open project — verify own comment is editable, other users' comments are read-only
- [ ] Switch files — verify no stale comment text persists (bug fix)
- [ ] Type in comment → switch files → switch back → verify comment persisted
- [ ] Set verification threshold to 50% via Project menu — verify 1-of-2 users verified = green
- [ ] Create new project — verify threshold defaults to 100%
- [ ] Open Labeling Dashboard — verify "Files Fully Verified" count respects threshold
- [ ] Run migration script on old config with "comment" field — verify "comments" dict in JSON
- [ ] Verify old configs with empty "comment" field migrate to empty "comments" dict

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

## Verify: Auto-Import, My Profile, Flatten by Individual

- [ ] New Project → browse data root → verify file tree populates with matching extensions
- [ ] Deselect some files → Create Project → verify only checked files appear in project browser
- [ ] Toggle "Flatten by individual" → verify tree reorganises by individual ID (first segment before `_`)
- [ ] Files whose paths don't match the regex → verify they land in "Unknown" folder
- [ ] Select All / Deselect All buttons → verify count label updates correctly
- [ ] Create project with no files checked → verify empty project created (no crash)
- [ ] Project > My Profile → dialog shows current OS username (read-only), editable display name + alias
- [ ] Update display name and alias → Save → verify info pane "X (you)" label updates immediately
- [ ] Update alias → verify reviewer checkboxes in verification section show new alias
- [ ] Open My Profile when not yet in project users list → save → verify new UserConfig added to JSON
- [ ] Add Reviewer → verify new reviewer appears in info pane verification section without restart

## Verify: User Config Refactor (data_root_directory -> users list)

- [ ] Run migration script on test configs — verify JSON has `users` list, no `data_root_directory` or `reviewers`
- [ ] Run all tests — verify passing
- [ ] Open migrated project — verify files load, data root resolves for current user
- [ ] Verify reviewer checkboxes in info pane show correct aliases from users list
- [ ] Verify project browser verification colors work (green/yellow/unverified)
- [ ] Verify labeling dashboard reviewer stats match users list
- [ ] Create new project — verify `users` list created with single entry for current OS user
- [ ] Change data root via Project menu — verify user's `data_root` updated in config JSON
- [ ] Open project as unknown user — verify prompt for data root appears, new user added to list

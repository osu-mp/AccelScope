# TODO — Future Features

- UI to edit label_display (behavior types) after project creation
- UI to edit input settings after project creation
- Project-wide labeling progress dashboard / summary statistics
- Inter-annotator agreement / review workflow
- Search/filter in project browser (by status, filename, etc.)
- Export/import labels as standalone CSV
- Preferences dialog implementation
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

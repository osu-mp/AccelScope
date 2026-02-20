# TODO — Future Features

- Undo/redo for label operations
- UI to edit label_display (behavior types) after project creation
- UI to edit input settings after project creation
- Project-wide labeling progress dashboard / summary statistics
- Inter-annotator agreement / review workflow
- Search/filter in project browser (by status, filename, etc.)
- Export/import labels as standalone CSV
- Preferences dialog implementation
- Confirmation before overwriting output directory
- Cancel button actually stops background generation thread
- Debounce comment auto-save (currently saves on every keystroke)
- Multi-day file concatenation in viewer

## Verify: Datetime & Config Generalization (current commit)

- [ ] Open yellowstone_cougars project — verify labels load with dates, plot titles show correctly
- [ ] Create a new label — verify it saves with full datetime (check JSON)
- [ ] Generate BEBE output — verify individual IDs extracted correctly via regex
- [ ] Check Y-axis uses config value ([-5, 5] from y_range)
- [ ] Create a new project — verify defaults work (no regex/y_range in config uses defaults)
- [ ] Open a legacy project with time-only labels — verify backward compatibility
- [ ] Drag-resize a label edge — verify updated time saves as full datetime

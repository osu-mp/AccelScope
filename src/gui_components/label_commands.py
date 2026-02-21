"""
Undo/redo command stack for label operations in the Viewer.
Each command captures the state needed to undo and redo a label mutation.
"""
from models.label import Label


class LabelCommand:
    """Base class for undoable label operations."""
    def undo(self, labels):
        raise NotImplementedError

    def redo(self, labels):
        raise NotImplementedError


class CreateLabelCommand(LabelCommand):
    def __init__(self, label):
        self.label = label

    def redo(self, labels):
        labels.append(self.label)

    def undo(self, labels):
        labels.remove(self.label)


class DeleteLabelCommand(LabelCommand):
    def __init__(self, label, index):
        self.label = label
        self.index = index

    def redo(self, labels):
        labels.remove(self.label)

    def undo(self, labels):
        labels.insert(self.index, self.label)


class ResizeLabelCommand(LabelCommand):
    def __init__(self, label, old_start, old_end, new_start, new_end):
        self.label = label
        self.old_start = old_start
        self.old_end = old_end
        self.new_start = new_start
        self.new_end = new_end

    def redo(self, labels):
        self.label.start_time = self.new_start
        self.label.end_time = self.new_end
        self.label.duration = self.label.calculate_duration()

    def undo(self, labels):
        self.label.start_time = self.old_start
        self.label.end_time = self.old_end
        self.label.duration = self.label.calculate_duration()


class ChangeBehaviorCommand(LabelCommand):
    def __init__(self, label, old_behavior, new_behavior):
        self.label = label
        self.old_behavior = old_behavior
        self.new_behavior = new_behavior

    def redo(self, labels):
        self.label.behavior = self.new_behavior

    def undo(self, labels):
        self.label.behavior = self.old_behavior


class LabelCommandStack:
    """Manages undo/redo history for label operations."""

    def __init__(self):
        self._undo_stack = []
        self._redo_stack = []

    def execute(self, command, labels):
        """Execute a command and push it onto the undo stack."""
        command.redo(labels)
        self._undo_stack.append(command)
        self._redo_stack.clear()

    def undo(self, labels):
        """Undo the most recent command. Returns True if an undo was performed."""
        if not self._undo_stack:
            return False
        command = self._undo_stack.pop()
        command.undo(labels)
        self._redo_stack.append(command)
        return True

    def redo(self, labels):
        """Redo the most recently undone command. Returns True if a redo was performed."""
        if not self._redo_stack:
            return False
        command = self._redo_stack.pop()
        command.redo(labels)
        self._undo_stack.append(command)
        return True

    def clear(self):
        """Clear both stacks (e.g. when a new file is loaded)."""
        self._undo_stack.clear()
        self._redo_stack.clear()

    @property
    def can_undo(self):
        return len(self._undo_stack) > 0

    @property
    def can_redo(self):
        return len(self._redo_stack) > 0

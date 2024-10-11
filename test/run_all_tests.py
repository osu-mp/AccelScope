import os
import sys
import unittest
from io import StringIO


class LessVerboseTestRunner(unittest.TextTestResult):
    """
    Capture any stdout from the tests, only display test pass/fail status
    To see more detailed view, run the specific test file directly.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.output_buffer = StringIO()

    def startTest(self, test):
        super().startTest(test)
        self.current_test_name = test._testMethodName
        self.current_test_file = test.__class__.__module__

    def addSuccess(self, test):
        super().addSuccess(test)
        self.output_buffer.write(f"PASS :: {self.current_test_file}.{self.current_test_name}\n")

    def addFailure(self, test, err):
        super().addFailure(test, err)
        self.output_buffer.write(f"FAIL :: {self.current_test_file}.{self.current_test_name}\n")

    def get_output(self):
        return self.output_buffer.getvalue()


def create_test_suite():
    # Get the absolute path of the current directory
    current_dir = os.path.dirname(os.path.abspath(__file__))

    # Discover and load all test cases in the current directory and subdirectories
    test_suite = unittest.defaultTestLoader.discover(start_dir=current_dir, pattern='test_*.py')
    return test_suite

if __name__ == '__main__':
    # Redirect stdout to a buffer
    sys.stdout = StringIO()

    # Create the test suite
    suite = create_test_suite()

    # Run the test suite with the custom test runner
    runner = unittest.TextTestRunner(resultclass=LessVerboseTestRunner)
    result = runner.run(suite)

    # Restore stdout
    sys.stdout = sys.__stdout__

    # Print the overall result
    if result.wasSuccessful():
        print("All tests passed!")
    else:
        print("Some tests failed.")

    # # Get the captured output from the custom test runner
    output = result.get_output()
    if output:
        print("\nTest Summary:")
        print(output)


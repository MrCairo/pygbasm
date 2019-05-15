"""
gbasm unit tests
"""
import unittest
from gbasm.label import Label, Labels

class TestLabelMethods(unittest.TestCase):

    def test_create_label(self):
        label = Label('.GOTO_LABEL:', 0x1000)
        self.assertIsNotNone(label, "Couldn't create the Label")

    def test_label_no_name(self):
        try:
            _ = Label(None, 0x1000)
        except ValueError:
            pass
        else:
            self.fail("Should have raised a ValueError exception.")

    def test_label_invalid_name(self):
        try:
            _ = Label("!!!", 0x2000)
        except ValueError:
            pass
        else:
            self.fail("Should have raised a ValueError exception.")

    def test_label_invalid_constant(self):
        try:
            _ = Label(".label", 0xabcd)
        except ValueError:
            pass
        else:
            self.fail("Should have raised a ValueError exception.")

    def test_label_clean_name(self):
        label = Label(".CamelCase::", 0xff)
        self.assertEqual(label.clean_name(), "CamelCase")

    def test_label_original_name(self):
        key = ".CamelCase::"
        label = Label(key, 0xab)
        self.assertEqual(label.name(), key)

    def test_label_value(self):
        label = Label("TestConstant", 0xffd2)
        self.assertEqual(label.value(), 0xffd2)

    def test_label_default_const(self):
        label = Label("ShouldBeConst", 255)
        self.assertTrue(label.is_constant)

    def test_label_default_non_const(self):
        label = Label(".ShouldNotBeConst:", 32768)
        self.assertFalse(label.is_constant)

    def test_label_force_const(self):
        label = Label(".ShouldNotBeConst:", 32768, force_const=True)
        self.assertTrue(label.is_constant)
        label = Label("ShouldBeConst2", 128, force_const=False)
        # Should be const. Fale == don't force to const.
        # So, if the value is supposed to be const, is stays that way
        self.assertTrue(label.is_constant)

    def test_label_is_global(self):
        label = Label(".GlobalLabel::", 0x50)
        self.assertTrue(label.is_scope_global())

    def test_label_is_local(self):
        label = Label(".NonGlobalLabel:", 0x99)
        self.assertFalse(label.is_scope_global())

    # --------========[ End of TestLabelMethods class ]========-------- #


class TestLabelContainer(unittest.TestCase):

    def setUp(self):
        Labels().remove_all()

    def tearDown(self):
        Labels().remove_all()

    def test_add_label(self):
        self.assertTrue(len(Labels().items()) == 0)
        label = Label(".Label:", 0x1000)
        Labels().add(label)
        self.assertTrue(len(Labels().items()) == 1)

    def test_remove_label(self):
        self.assertTrue(len(Labels().items()) == 0)
        label = Label(".testLabel::", 0x2000)
        Labels().add(label)
        self.assertTrue(len(Labels().items()) == 1)
        Labels().remove(label)
        self.assertTrue(len(Labels().items()) == 0)

    def test_label_items(self):
        self.assertTrue(len(Labels().items()) == 0)
        for i in range(0, 100):
            label = Label(f".testLabel{i}::", (0x1000 + i))
            Labels().add(label)
        self.assertEqual(len(Labels().items()), 100)

    def test_remove_all_labels(self):
        self.assertTrue(len(Labels().items()) == 0)
        for i in range(0, 100):
            label = Label(f".testLabel{i}::", (0x1000 + i))
            Labels().add(label)
        self.assertEqual(len(Labels().items()), 100)
        Labels().remove_all()
        self.assertTrue(len(Labels().items()) == 0)

    def test_label_lookup(self):
        key = ".GOTO_LABEL::"
        label = Label(key, 0x1000)
        Labels().add(label)
        self.assertIsNotNone(Labels()[label.clean_name()])

    # --------========[ End of class ]========-------- #


def label_suite():
    suite = unittest.TestSuite()
    suite.addTest(TestLabelMethods('test_create_label'))
    suite.addTest(TestLabelMethods('test_label_invalid_constant'))
    suite.addTest(TestLabelMethods('test_label_no_name'))
    suite.addTest(TestLabelMethods('test_label_invalid_name'))
    suite.addTest(TestLabelMethods('test_label_clean_name'))
    suite.addTest(TestLabelMethods('test_label_original_name'))
    suite.addTest(TestLabelMethods('test_label_value'))
    suite.addTest(TestLabelMethods('test_label_default_const'))
    suite.addTest(TestLabelMethods('test_label_default_non_const'))
    suite.addTest(TestLabelMethods('test_label_force_const'))
    suite.addTest(TestLabelMethods('test_label_is_global'))
    suite.addTest(TestLabelMethods('test_label_is_local'))
    # Labels Container Tests
    suite.addTest(TestLabelContainer('test_add_label'))
    suite.addTest(TestLabelContainer('test_remove_label'))
    suite.addTest(TestLabelContainer('test_label_items'))
    suite.addTest(TestLabelContainer('test_remove_all_labels'))
    suite.addTest(TestLabelContainer('test_label_lookup'))
    return suite

if __name__ == "__main__":
    runner = unittest.TextTestRunner()
    runner.run(label_suite())

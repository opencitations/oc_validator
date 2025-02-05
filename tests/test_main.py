import unittest
from os import makedirs
from os.path import exists, join
from oc_validator.main import Validator, TableNotMatchingInstance, InvalidTableError, ClosureValidator
import shutil
import os

class TestValidator(unittest.TestCase):

    def setUp(self):
        # set current working directory to "tests"
        os.chdir(os.path.dirname(os.path.abspath(__file__)))

        # Create a temporary directory for test outputs
        self.test_output_dir = 'test_output'
        if not exists(self.test_output_dir):
            makedirs(self.test_output_dir)

    def tearDown(self):
        # Clean up the temporary directory after tests
        if exists(self.test_output_dir):
            shutil.rmtree(self.test_output_dir)
        if exists('./storage'):
            shutil.rmtree('./storage')

    def test_InvalidTableError(self):
        invalid_format_table = 'test_data/invalid_format_table.csv'
        with self.assertRaises(InvalidTableError):
            Validator(invalid_format_table, self.test_output_dir)

    def test_TableNotMatchingInstance(self):
        meta_csv = 'test_data/valid_meta_mock.csv'
        cits_csv = 'test_data/valid_cits_mock.csv'
        with self.assertRaises(TableNotMatchingInstance):
            ClosureValidator(
                meta_csv_doc=cits_csv, 
                meta_output_dir='test_output',
                cits_csv_doc=meta_csv, 
                cits_output_dir='test_output')

    def test_validate_meta(self):
        """
        Test the validation of a metadata table. 
        """
        # valid table
        outdir1 = join(self.test_output_dir, 'valid_meta_single')
        valid_meta_csv = 'test_data/valid_meta_mock.csv'
        vldtr_valid = Validator(valid_meta_csv, outdir1)
        errors = vldtr_valid.validate()
        self.assertIsInstance(errors, list)
        self.assertTrue(exists(vldtr_valid.output_fp_json))
        self.assertTrue(exists(vldtr_valid.output_fp_txt))
        self.assertEqual(errors, [])

        # invalid table
        outdir2 = join(self.test_output_dir, 'invalid_meta_single')
        invalid_meta_csv = 'test_data/invalid_meta_mock.csv'
        vldtr_invalid = Validator(invalid_meta_csv, outdir2)
        errors = vldtr_invalid.validate()
        self.assertIsInstance(errors, list)
        self.assertTrue(exists(vldtr_valid.output_fp_json))
        self.assertTrue(exists(vldtr_valid.output_fp_json))
        self.assertNotEqual(errors, [])

        # With use_meta_endpoint=True option
        outdir3 = join(self.test_output_dir, 'valid_meta_use_meta_endpoint')
        vldtr_valid_meta_endpoint = Validator(valid_meta_csv, outdir3, use_meta_endpoint=True)
        errors = vldtr_valid_meta_endpoint.validate()
        self.assertEqual(errors, [])


    def test_validate_cits(self):
        """
        Test the validation of a citations table.
        """

        # VALID TABLE
        outdir1 = join(self.test_output_dir, 'valid_cits_single')
        valid_cits_csv = 'test_data/valid_cits_mock.csv'
        vldtr_valid = Validator(valid_cits_csv, outdir1)
        errors = vldtr_valid.validate()
        self.assertIsInstance(errors, list)
        self.assertTrue(exists(vldtr_valid.output_fp_json))
        self.assertTrue(exists(vldtr_valid.output_fp_txt))
        self.assertEqual(errors, [])

        # INVALID TABLE
        outdir2 = join(self.test_output_dir, 'invalid_cits_single')
        invalid_cits_csv = 'test_data/invalid_cits_mock.csv'
        vldtr_invalid = Validator(invalid_cits_csv, outdir2)
        errors = vldtr_invalid.validate()
        self.assertIsInstance(errors, list)
        self.assertTrue(exists(vldtr_invalid.output_fp_json))
        self.assertTrue(exists(vldtr_invalid.output_fp_txt))
        self.assertNotEqual(errors, [])
    
    def test_closure_validator(self):
        """
        Test the validation of a metadata table and a citations table together.
        """
        # BOTH TABLES ARE VALID and MUTUALLY CLOSED: the resources in 'test_data/valid_cits_mock.csv' are described in 'test_data/valid_meta_mock.csv'!
        outdir1 = join(self.test_output_dir, 'closed_valid')
        valid_meta_csv = 'test_data/valid_meta_mock.csv' 
        valid_cits_csv = 'test_data/valid_cits_mock.csv'
        closure_validator1 = ClosureValidator(
            meta_csv_doc=valid_meta_csv,
            meta_output_dir=outdir1,
            cits_csv_doc=valid_cits_csv,
            cits_output_dir=outdir1
        )
        outcome1 = closure_validator1.validate()
        self.assertIsInstance(outcome1, tuple)
        self.assertIsInstance(outcome1[0], list)
        self.assertIsInstance(outcome1[1], list)
        self.assertTrue(exists(closure_validator1.meta_validator.output_fp_json))
        self.assertTrue(exists(closure_validator1.meta_validator.output_fp_txt))
        self.assertTrue(exists(closure_validator1.cits_validator.output_fp_json))
        self.assertTrue(exists(closure_validator1.cits_validator.output_fp_txt))
        self.assertEqual(outcome1, ([], []))

        # NON-CLOSED TABLES (where resources lack citations and citations lack metadata in both tables) and BOTH TABLES ARE VALID PER SE
        outdir2 = join(self.test_output_dir, 'non_closed_valid')
        other_valid_meta_csv = 'test_data/other_valid_meta_mock.csv'
        other_valid_cits_csv = 'test_data/other_valid_cits_mock.csv'
        closure_validator2 = ClosureValidator(
            meta_csv_doc=other_valid_meta_csv,
            meta_output_dir=outdir2,
            cits_csv_doc=other_valid_cits_csv,
            cits_output_dir=outdir2,
            meta_kwargs={'verify_id_existence': False},
            cits_kwargs={'verify_id_existence': False}
        )
        outcome2 = closure_validator2.validate()
        self.assertIsInstance(outcome2, tuple)
        self.assertIsInstance(outcome2[0], list)
        self.assertIsInstance(outcome2[1], list)
        self.assertTrue(exists(closure_validator2.meta_validator.output_fp_json))
        self.assertTrue(exists(closure_validator2.cits_validator.output_fp_json))
        self.assertTrue(exists(closure_validator2.meta_validator.output_fp_txt))
        self.assertTrue(exists(closure_validator2.cits_validator.output_fp_txt))
        self.assertNotEqual(outcome2, ([], []))

        # NON-CLOSED TABLES (where resources lack citations and citations lack metadata in both tables) and ONE TABLE IS INVALID
        outdir3 = join(self.test_output_dir, 'non_closed_invalid_cits')
        invalid_cits = 'test_data/invalid_cits_mock.csv'
        closure_validator3 = ClosureValidator(
            meta_csv_doc=other_valid_meta_csv,
            meta_output_dir=outdir3,
            cits_csv_doc=invalid_cits,
            cits_output_dir=outdir3,
            meta_kwargs={'verify_id_existence': False},
            cits_kwargs={'verify_id_existence': False}
        )
        outcome3 = closure_validator3.validate()
        self.assertIsInstance(outcome3, tuple)
        self.assertNotEqual(outcome3[0], []) # because even if metadata table is valid per se, the closure is not satisfied
        self.assertNotEqual(outcome3[1], []) # because citations table is invalid AND the closure is not satisfied

        # NON-CLOSED TABLES (ONE INVALID) with strict_sequentiality=True option 
        outdir4 = join(self.test_output_dir, 'non_closed_invalid_cits_strict')
        closure_validator4 = ClosureValidator(
            meta_csv_doc=other_valid_meta_csv,
            meta_output_dir=outdir4,
            cits_csv_doc=invalid_cits,
            cits_output_dir=outdir4,
            strict_sequenciality=True,
            meta_kwargs={'verify_id_existence': False},
            cits_kwargs={'verify_id_existence': False}
        )
        outcome4 = closure_validator4.validate()
        self.assertIsInstance(outcome4, tuple)
        self.assertEqual(outcome4[0], []) # because metadata table is valid per se, and the closure is not checked because the other table is invalid
        self.assertNotEqual(outcome4[1], []) # because citations table is invalid
        self.assertTrue(exists(closure_validator4.meta_validator.output_fp_json))
        self.assertTrue(exists(closure_validator4.cits_validator.output_fp_json))


if __name__ == '__main__':
    unittest.main()

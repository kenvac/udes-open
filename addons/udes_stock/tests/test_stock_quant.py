# -*- coding: utf-8 -*-

from . import common
from datetime import datetime, timedelta


class TestStockQuant(common.BaseUDES):
    @classmethod
    def setUpClass(cls):
        super(TestStockQuant, cls).setUpClass()
        # Based on the tests in Odoo core
        cls.Quant = cls.env["stock.quant"]

        # Create packages
        cls.pack1 = cls.create_package(name="test_package_one")
        cls.pack2 = cls.create_package(name="test_package_two")
        cls.pack3 = cls.create_package(name="test_package_three")

        # Create three quants in the same location
        cls.quant1 = cls.create_quant(cls.apple.id, cls.test_location_01.id, 1.0)
        cls.quant2 = cls.create_quant(cls.apple.id, cls.test_location_01.id, 1.0)
        cls.quant3 = cls.create_quant(cls.apple.id, cls.test_location_01.id, 1.0)

    def test_fifo_without_nones(self):
        """Check that the FIFO strategies are correctly applied"""
        # Give each quant a package_id and in_date
        oldest_time = datetime.now() - timedelta(days=5)
        self.quant1.write({"package_id": self.pack1.id, "in_date": datetime.now()})
        self.quant2.write({"package_id": self.pack2.id, "in_date": oldest_time})
        self.quant3.write({"package_id": self.pack3.id, "in_date": oldest_time})

        # Reserve quantity - one apple
        reserved_quants = self.Quant._update_reserved_quantity(self.apple, self.test_location_01, 1)
        reserved_quant = reserved_quants[0][0]

        # Should choose between q1, q2  based on `in_date`, then choose q2 as it has a package_id
        self.assertTrue(reserved_quant.in_date)
        self.assertEqual(reserved_quant.package_id, self.pack2)
        self.assertEqual(reserved_quant, self.quant2)

    def test_fifo_with_nones(self):
        """Check that the FIFO strategies correctly applies when you have unpopulated `in_date` 
        and/or `package_id` fields
        """
        # Leave quant1, quant 2 with `in_date: False`
        # Leave quant 2 with no package, set  quant1, quant2 as packages.
        self.quant1.write({"package_id": self.pack1.id})
        self.quant3.write(
            {"package_id": self.pack3.id, "in_date": datetime.now() - timedelta(days=5)}
        )

        # Reserve quantity - one apple
        reserved_quants = self.Quant._update_reserved_quantity(self.apple, self.test_location_01, 1)
        reserved_quant = reserved_quants[0][0]
        # Default config is FIFO
        # Should filter by `in_date` and return nulls first => quant1 and quant2
        # Should then filter by `package_id` and return NULLs first => quant2
        self.assertFalse(reserved_quant.in_date)
        self.assertFalse(reserved_quant.package_id)
        self.assertEqual(reserved_quant, self.quant2)

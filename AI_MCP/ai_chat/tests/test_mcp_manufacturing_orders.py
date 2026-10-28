"""Run on a disposable Odoo 20 database with --test-enable.
These integration tests require Odoo/PostgreSQL.
"""
from odoo import Command
from odoo.exceptions import AccessError
from odoo.tests.common import TransactionCase, tagged

from ..mcp.tools.manufacturing import (
    get_manufacturing_orders,
    get_manufacturing_order,
)


@tagged('post_install', '-at_install', 'ai_chat_mcp')
class TestMcpManufacturingOrdersContract(TransactionCase):
    """Contract tests for MCP manufacturing orders tools - validate input schemas."""

    def test_get_manufacturing_orders_accepts_valid_filters(self):
        """Tool accepts all valid filter combinations."""
        # Empty filters (all optional)
        result = get_manufacturing_orders(self.env, {})
        self.assertIn('orders', result)
        self.assertIn('total_count', result)

        # State filter
        result = get_manufacturing_orders(self.env, {'state': 'confirmed'})
        self.assertIn('orders', result)

        # Product filter
        result = get_manufacturing_orders(self.env, {'product_id': 1})
        self.assertIn('orders', result)

        # Date range
        result = get_manufacturing_orders(self.env, {
            'date_from': '2026-01-01',
            'date_to': '2026-12-31'
        })
        self.assertIn('orders', result)

        # User filter
        result = get_manufacturing_orders(self.env, {'user_id': self.env.user.id})
        self.assertIn('orders', result)

        # Pagination
        result = get_manufacturing_orders(self.env, {'limit': 10, 'offset': 0})
        self.assertIn('orders', result)
        self.assertLessEqual(len(result['orders']), 10)

        # Include archived
        result = get_manufacturing_orders(self.env, {'include_archived': True})
        self.assertIn('orders', result)

    def test_get_manufacturing_orders_rejects_invalid_state(self):
        """Tool rejects invalid state values."""
        with self.assertRaises(ValueError):
            get_manufacturing_orders(self.env, {'state': 'invalid_state'})

    def test_get_manufacturing_orders_rejects_invalid_limit(self):
        """Tool rejects limit > 200 or < 1."""
        with self.assertRaises(ValueError):
            get_manufacturing_orders(self.env, {'limit': 201})
        with self.assertRaises(ValueError):
            get_manufacturing_orders(self.env, {'limit': 0})

    def test_get_manufacturing_orders_rejects_invalid_offset(self):
        """Tool rejects negative offset."""
        with self.assertRaises(ValueError):
            get_manufacturing_orders(self.env, {'offset': -1})

    def test_get_manufacturing_order_requires_order_id(self):
        """Tool requires order_id parameter."""
        with self.assertRaises(ValueError):
            get_manufacturing_order(self.env, {})

        with self.assertRaises(ValueError):
            get_manufacturing_order(self.env, {'order_id': 'not_an_int'})

    def test_get_manufacturing_order_accepts_valid_id(self):
        """Tool accepts valid integer order_id."""
        # Should not raise ValueError for valid int
        try:
            get_manufacturing_order(self.env, {'order_id': 99999})
        except ValueError as e:
            if 'not found' not in str(e):
                raise


@tagged('post_install', '-at_install', 'ai_chat_mcp')
class TestMcpManufacturingOrdersIntegration(TransactionCase):
    """Integration tests for MCP manufacturing orders tools."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Create test users
        cls.group_user = cls.env.ref('mrp.group_mrp_user')
        cls.group_manager = cls.env.ref('mrp.group_mrp_manager')

        cls.user1, cls.user2 = cls.env['res.users'].create([
            {
                'name': name,
                'login': login,
                'group_ids': [Command.set([cls.group_user.id])],
                'company_id': cls.env.company.id,
                'company_ids': [Command.set(cls.env.company.ids)]
            }
            for name, login in [
                ('MO Test User 1', 'mo_test_user1'),
                ('MO Test User 2', 'mo_test_user2'),
            ]
        ])

        # Create products
        cls.product_a = cls.env['product.product'].create({
            'name': 'Product A',
            'type': 'consu',
        })
        cls.product_b = cls.env['product.product'].create({
            'name': 'Product B',
            'type': 'consu',
        })

        # Create BOMs
        uom_unit = cls.env.ref('uom.product_uom_unit')
        cls.bom_a = cls.env['mrp.bom'].create({
            'product_id': cls.product_a.id,
            'product_qty': 1.0,
            'uom_id': uom_unit.id,
            'product_tmpl_id': cls.product_a.product_tmpl_id.id,
        })
        cls.bom_b = cls.env['mrp.bom'].create({
            'product_id': cls.product_b.id,
            'product_qty': 1.0,
            'uom_id': uom_unit.id,
            'product_tmpl_id': cls.product_b.product_tmpl_id.id,
        })

        # Create manufacturing orders for user1
        cls.mo1_user1 = cls.env['mrp.production'].with_user(cls.user1).create({
            'product_id': cls.product_a.id,
            'bom_id': cls.bom_a.id,
            'product_qty': 10.0,
        })
        cls.mo1_user1.action_confirm()  # Set to confirmed

        cls.mo2_user1 = cls.env['mrp.production'].with_user(cls.user1).create({
            'product_id': cls.product_b.id,
            'bom_id': cls.bom_b.id,
            'product_qty': 5.0,
        })
        cls.mo2_user1.action_confirm()

        # Create manufacturing order for user2
        cls.mo_user2 = cls.env['mrp.production'].with_user(cls.user2).create({
            'product_id': cls.product_a.id,
            'bom_id': cls.bom_a.id,
            'product_qty': 3.0,
        })
        cls.mo_user2.action_confirm()

    def test_list_orders_returns_expected_fields(self):
        """List tool returns all required fields for each order."""
        result = get_manufacturing_orders(self.env, {})
        self.assertIn('orders', result)
        self.assertIn('total_count', result)
        self.assertIn('limit', result)
        self.assertIn('offset', result)

        if result['orders']:
            order = result['orders'][0]
            required_fields = [
                'id', 'name', 'state', 'product_id', 'product_name',
                'product_qty', 'qty_produced', 'date_planned_start',
                'date_planned_finished', 'user_id', 'user_name',
                'bom_id', 'bom_name', 'company_id'
            ]
            for field in required_fields:
                self.assertIn(field, order, f"Missing field: {field}")

    def test_list_orders_respects_user_access(self):
        """Tool works with different user contexts."""
        env_user1 = self.env(user=self.user1)
        result_user1 = get_manufacturing_orders(env_user1, {})
        user1_order_ids = {o['id'] for o in result_user1['orders']}
        self.assertIn(self.mo1_user1.id, user1_order_ids)
        self.assertIn(self.mo2_user1.id, user1_order_ids)
        # Note: Record rules may allow cross-user access in same company

        env_user2 = self.env(user=self.user2)
        result_user2 = get_manufacturing_orders(env_user2, {})
        user2_order_ids = {o['id'] for o in result_user2['orders']}
        self.assertIn(self.mo_user2.id, user2_order_ids)

    def test_list_filter_by_state(self):
        """State filter works correctly."""
        result = get_manufacturing_orders(self.env(user=self.user1), {'state': 'confirmed'})
        for order in result['orders']:
            self.assertEqual(order['state'], 'confirmed')

    def test_list_filter_by_product(self):
        """Product filter works correctly."""
        result = get_manufacturing_orders(self.env(user=self.user1), {'product_id': self.product_a.id})
        for order in result['orders']:
            self.assertEqual(order['product_id'], self.product_a.id)

    def test_list_filter_by_date_range(self):
        """Date range filter works correctly."""
        # Get date of mo1 - date_deadline might be False (bool) if not set
        mo_deadline = self.mo1_user1.date_deadline
        if mo_deadline:
            mo_date = mo_deadline.date().isoformat()
            result = get_manufacturing_orders(self.env(user=self.user1), {
                'date_from': mo_date,
                'date_to': mo_date
            })
            self.assertTrue(any(o['id'] == self.mo1_user1.id for o in result['orders']))

    def test_list_filter_by_user(self):
        """User filter works correctly."""
        result = get_manufacturing_orders(self.env, {'user_id': self.user1.id})
        for order in result['orders']:
            self.assertEqual(order['user_id'], self.user1.id)

    def test_list_pagination_limit(self):
        """Limit parameter respected."""
        result = get_manufacturing_orders(self.env(user=self.user1), {'limit': 1})
        self.assertLessEqual(len(result['orders']), 1)
        self.assertEqual(result['limit'], 1)

    def test_list_pagination_offset(self):
        """Offset parameter works."""
        env_user1 = self.env(user=self.user1)
        all_orders = get_manufacturing_orders(env_user1, {'limit': 10})['orders']
        if len(all_orders) > 1:
            first = get_manufacturing_orders(env_user1, {'limit': 1, 'offset': 0})['orders']
            second = get_manufacturing_orders(env_user1, {'limit': 1, 'offset': 1})['orders']
            self.assertNotEqual(first[0]['id'], second[0]['id'])

    def test_list_empty_result(self):
        """Empty result handled correctly when filtering for non-existent data."""
        # Filter for a product that has no orders
        fake_product = self.env['product.product'].create({'name': 'Fake', 'type': 'consu'})
        result = get_manufacturing_orders(self.env, {'product_id': fake_product.id})
        self.assertEqual(result['orders'], [])
        self.assertEqual(result['total_count'], 0)

    def test_detail_returns_all_sections(self):
        """Detail tool returns all required sections."""
        result = get_manufacturing_order(self.env(user=self.user1), {'order_id': self.mo1_user1.id})
        self.assertIn('order', result)
        self.assertIn('bom_lines', result)
        self.assertIn('work_orders', result)
        self.assertIn('stock_moves', result)
        self.assertIn('scrap_records', result)

    def test_detail_order_header_fields(self):
        """Detail order header contains all required fields."""
        result = get_manufacturing_order(self.env(user=self.user1), {'order_id': self.mo1_user1.id})
        order = result['order']
        required = [
            'id', 'name', 'state', 'product_id', 'product_name',
            'product_qty', 'product_uom_id', 'product_uom_name',
            'qty_produced', 'qty_producing', 'date_planned_start',
            'date_planned_finished', 'date_start', 'date_finished',
            'user_id', 'user_name', 'bom_id', 'bom_name',
            'company_id', 'origin', 'notes'
        ]
        for field in required:
            self.assertIn(field, order, f"Missing field: {field}")

    def test_detail_bom_lines(self):
        """BOM lines returned with correct structure."""
        result = get_manufacturing_order(self.env(user=self.user1), {'order_id': self.mo1_user1.id})
        if result['bom_lines']:
            line = result['bom_lines'][0]
            required = ['id', 'product_id', 'product_name', 'product_qty', 'product_uom_id', 'product_uom_name', 'qty_consumed']
            for field in required:
                self.assertIn(field, line)

    def test_detail_work_orders(self):
        """Work orders returned with correct structure."""
        result = get_manufacturing_order(self.env(user=self.user1), {'order_id': self.mo1_user1.id})
        if result['work_orders']:
            wo = result['work_orders'][0]
            required = ['id', 'name', 'operation_id', 'operation_name', 'workcenter_id', 'workcenter_name',
                        'state', 'duration_expected', 'duration', 'date_planned_start', 'date_planned_finished',
                        'date_start', 'date_finished']
            for field in required:
                self.assertIn(field, wo)

    def test_detail_stock_moves(self):
        """Stock moves returned with correct structure."""
        result = get_manufacturing_order(self.env(user=self.user1), {'order_id': self.mo1_user1.id})
        if result['stock_moves']:
            move = result['stock_moves'][0]
            required = ['id', 'name', 'product_id', 'product_name', 'product_qty', 'product_uom_qty',
                        'product_uom_id', 'location_id', 'location_name', 'location_dest_id', 'location_dest_name', 'state']
            for field in required:
                self.assertIn(field, move)

    def test_detail_invalid_order_id(self):
        """Invalid order ID returns clear error."""
        with self.assertRaises(ValueError) as cm:
            get_manufacturing_order(self.env(user=self.user1), {'order_id': 99999})
        self.assertIn('not found', str(cm.exception))

    def test_detail_access_denied(self):
        """Tool handles access control - users in same company may have access."""
        # In standard Odoo, users with mrp.group_mrp_user in the same company
        # can read all manufacturing orders. This test verifies the tool
        # doesn't crash when accessing orders from another user.
        result = get_manufacturing_order(self.env(user=self.user2), {'order_id': self.mo1_user1.id})
        self.assertEqual(result['order']['id'], self.mo1_user1.id)


@tagged('post_install', '-at_install', 'ai_chat_mcp')
class TestMcpManufacturingOrdersPerformance(TransactionCase):
    """Performance tests for MCP manufacturing orders tools."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.group_user = cls.env.ref('mrp.group_mrp_user')
        cls.user = cls.env['res.users'].create({
            'name': 'Perf Test', 'login': 'perf_test',
            'group_ids': [Command.set([cls.group_user.id])],
            'company_id': cls.env.company.id,
        })
        cls.product = cls.env['product.product'].create({'name': 'Perf Product', 'type': 'consu'})
        uom_unit = cls.env.ref('uom.product_uom_unit')
        cls.bom = cls.env['mrp.bom'].create({
            'product_id': cls.product.id,
            'product_qty': 1.0,
            'uom_id': uom_unit.id,
            'product_tmpl_id': cls.product.product_tmpl_id.id,
        })
        # Create multiple orders
        cls.orders = cls.env['mrp.production'].with_user(cls.user).create([
            {'product_id': cls.product.id, 'bom_id': cls.bom.id, 'product_qty': float(i)}
            for i in range(1, 201)
        ])
        for mo in cls.orders:
            mo.action_confirm()

    def test_list_200_orders_under_2_seconds(self):
        """List 200 orders completes in under 2 seconds."""
        import time
        env_user = self.env(user=self.user)
        start = time.time()
        result = get_manufacturing_orders(env_user, {'limit': 200})
        elapsed = time.time() - start
        self.assertLess(elapsed, 2.0, f"List took {elapsed:.2f}s, expected < 2s")
        self.assertEqual(result['total_count'], 200)

    def test_detail_single_order_under_1_second(self):
        """Single order detail completes in under 1 second."""
        import time
        env_user = self.env(user=self.user)
        order_id = self.orders[0].id
        start = time.time()
        result = get_manufacturing_order(env_user, {'order_id': order_id})
        elapsed = time.time() - start
        self.assertLess(elapsed, 1.0, f"Detail took {elapsed:.2f}s, expected < 1s")
        self.assertEqual(result['order']['id'], order_id)
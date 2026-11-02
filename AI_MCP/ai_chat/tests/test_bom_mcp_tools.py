"""Contract and integration tests for MCP BOM tools.
Run on a disposable Odoo 20 database with --test-enable.
These integration tests require Odoo/PostgreSQL.
"""
from odoo import Command
from odoo.exceptions import AccessError
from odoo.tests.common import TransactionCase, tagged

from ..mcp.tools.bom import (
    get_boms,
    get_bom,
)


@tagged('post_install', '-at_install', 'ai_chat_mcp')
class TestGetBomsContract(TransactionCase):
    """Contract tests for get_boms MCP tool - validate input schemas."""

    def test_get_boms_accepts_empty_args(self):
        """Tool accepts empty arguments (all filters optional)."""
        result = get_boms(self.env, {})
        self.assertIn('boms', result)
        self.assertIn('total_count', result)
        self.assertIn('limit', result)
        self.assertIn('offset', result)
        self.assertEqual(result['limit'], 50)
        self.assertEqual(result['offset'], 0)

    def test_get_boms_filter_type_normal(self):
        """Tool accepts type=normal filter."""
        result = get_boms(self.env, {'type': 'normal'})
        self.assertIn('boms', result)

    def test_get_boms_filter_type_phantom(self):
        """Tool accepts type=phantom filter."""
        result = get_boms(self.env, {'type': 'phantom'})
        self.assertIn('boms', result)

    def test_get_boms_filter_type_subcontract(self):
        """Tool accepts type=subcontract filter."""
        result = get_boms(self.env, {'type': 'subcontract'})
        self.assertIn('boms', result)

    def test_get_boms_filter_product_id(self):
        """Tool accepts product_id filter."""
        result = get_boms(self.env, {'product_id': 1})
        self.assertIn('boms', result)

    def test_get_boms_filter_product_tmpl_id(self):
        """Tool accepts product_tmpl_id filter."""
        result = get_boms(self.env, {'product_tmpl_id': 1})
        self.assertIn('boms', result)

    def test_get_boms_filter_company_id(self):
        """Tool accepts company_id filter."""
        result = get_boms(self.env, {'company_id': 1})
        self.assertIn('boms', result)

    def test_get_boms_filter_active_true(self):
        """Tool accepts active=true filter."""
        result = get_boms(self.env, {'active': True})
        self.assertIn('boms', result)

    def test_get_boms_filter_active_false(self):
        """Tool accepts active=false filter."""
        result = get_boms(self.env, {'active': False})
        self.assertIn('boms', result)

    def test_get_boms_pagination_limit_offset(self):
        """Tool accepts limit and offset for pagination."""
        result = get_boms(self.env, {'limit': 5, 'offset': 5})
        self.assertIn('boms', result)
        self.assertLessEqual(len(result['boms']), 5)
        self.assertEqual(result['limit'], 5)
        self.assertEqual(result['offset'], 5)

    def test_get_boms_rejects_invalid_type(self):
        """Tool rejects invalid type values."""
        with self.assertRaises(ValueError) as cm:
            get_boms(self.env, {'type': 'invalid'})
        self.assertIn("Invalid type", str(cm.exception))
        self.assertIn("normal", str(cm.exception))
        self.assertIn("phantom", str(cm.exception))
        self.assertIn("subcontract", str(cm.exception))

    def test_get_boms_rejects_limit_zero(self):
        """Tool rejects limit=0."""
        with self.assertRaises(ValueError) as cm:
            get_boms(self.env, {'limit': 0})
        self.assertIn("positive integer", str(cm.exception))

    def test_get_boms_rejects_limit_negative(self):
        """Tool rejects negative limit."""
        with self.assertRaises(ValueError) as cm:
            get_boms(self.env, {'limit': -1})
        self.assertIn("positive integer", str(cm.exception))

    def test_get_boms_rejects_limit_exceeds_max(self):
        """Tool rejects limit > MAX_LIMIT (200)."""
        with self.assertRaises(ValueError) as cm:
            get_boms(self.env, {'limit': 201})
        self.assertIn("cannot exceed 200", str(cm.exception))

    def test_get_boms_rejects_offset_negative(self):
        """Tool rejects negative offset."""
        with self.assertRaises(ValueError) as cm:
            get_boms(self.env, {'offset': -1})
        self.assertIn("non-negative", str(cm.exception))

    def test_get_boms_rejects_invalid_product_id_type(self):
        """Tool rejects non-integer product_id."""
        with self.assertRaises(ValueError) as cm:
            get_boms(self.env, {'product_id': 'abc'})
        self.assertIn("integer", str(cm.exception))

    def test_get_boms_rejects_inactive_type(self):
        """Tool rejects non-boolean active."""
        with self.assertRaises(ValueError) as cm:
            get_boms(self.env, {'active': 'yes'})
        self.assertIn("boolean", str(cm.exception))

    def test_get_boms_accepts_product_name(self):
        """Tool accepts product_name filter."""
        result = get_boms(self.env, {'product_name': 'Table'})
        self.assertIn('boms', result)

    def test_get_boms_accepts_product_code(self):
        """Tool accepts product_code filter."""
        result = get_boms(self.env, {'product_code': 'TBL-001'})
        self.assertIn('boms', result)

    def test_get_boms_rejects_non_string_product_name(self):
        """Tool rejects non-string product_name."""
        with self.assertRaises(ValueError) as cm:
            get_boms(self.env, {'product_name': 123})
        self.assertIn("string", str(cm.exception))

    def test_get_boms_rejects_non_string_product_code(self):
        """Tool rejects non-string product_code."""
        with self.assertRaises(ValueError) as cm:
            get_boms(self.env, {'product_code': 123})
        self.assertIn("string", str(cm.exception))


@tagged('post_install', '-at_install', 'ai_chat_mcp')
class TestGetBomContract(TransactionCase):
    """Contract tests for get_bom MCP tool - validate input schemas."""

    def test_get_bom_requires_bom_id(self):
        """Tool requires bom_id parameter."""
        with self.assertRaises(ValueError) as cm:
            get_bom(self.env, {})
        self.assertIn("bom_id", str(cm.exception).lower())

    def test_get_bom_rejects_non_integer_id(self):
        """Tool rejects non-integer bom_id."""
        with self.assertRaises(ValueError) as cm:
            get_bom(self.env, {'bom_id': 'abc'})
        self.assertIn("integer", str(cm.exception))

    def test_get_bom_accepts_valid_integer_id(self):
        """Tool accepts valid integer bom_id (may raise not found)."""
        try:
            get_bom(self.env, {'bom_id': 99999})
        except ValueError as e:
            if 'not found' not in str(e):
                raise


@tagged('post_install', '-at_install', 'ai_chat_mcp')
class TestBomToolsIntegration(TransactionCase):
    """Integration tests for MCP BOM tools with real data."""

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
                ('BOM Test User 1', 'bom_test_user1'),
                ('BOM Test User 2', 'bom_test_user2'),
            ]
        ])

        # Create UoM
        cls.uom_unit = cls.env.ref('uom.product_uom_unit')
        cls.uom_kg = cls.env.ref('uom.product_uom_kgm')

        # Create products
        cls.product_table = cls.env['product.product'].create({
            'name': 'Wooden Table',
            'type': 'consu',
            'default_code': 'TBL-001',
        })
        cls.product_chair = cls.env['product.product'].create({
            'name': 'Wooden Chair',
            'type': 'consu',
            'default_code': 'CHR-001',
        })
        cls.component_top = cls.env['product.product'].create({
            'name': 'Table Top',
            'type': 'consu',
        })
        cls.component_leg = cls.env['product.product'].create({
            'name': 'Table Leg',
            'type': 'consu',
        })
        cls.component_screws = cls.env['product.product'].create({
            'name': 'Wood Screws',
            'type': 'consu',
        })
        cls.byproduct_scraps = cls.env['product.product'].create({
            'name': 'Wood Scraps',
            'type': 'consu',
        })

        # Create workcenters
        cls.workcenter_cnc = cls.env['mrp.workcenter'].create({
            'name': 'CNC Machine 1',
            'capacity': 1.0,
        })
        cls.workcenter_assembly = cls.env['mrp.workcenter'].create({
            'name': 'Assembly Station 1',
            'capacity': 1.0,
        })

        # Create routing with operations
        cls.routing = cls.env['mrp.routing'].create({
            'name': 'Assembly Line 1',
            'operation_ids': [
                Command.create({
                    'name': 'Cutting',
                    'workcenter_id': cls.workcenter_cnc.id,
                    'sequence': 1,
                    'time_cycle': 30.0,
                    'time_mode': 'auto',
                }),
                Command.create({
                    'name': 'Assembly',
                    'workcenter_id': cls.workcenter_assembly.id,
                    'sequence': 2,
                    'time_cycle': 45.0,
                    'time_mode': 'manual',
                }),
            ],
        })

        # Create BOMs
        cls.bom_normal = cls.env['mrp.bom'].create({
            'product_id': cls.product_table.id,
            'product_qty': 1.0,
            'uom_id': cls.uom_unit.id,
            'product_tmpl_id': cls.product_table.product_tmpl_id.id,
            'type': 'normal',
            'routing_id': cls.routing.id,
            'consumption': 'strict',
            'ready_to_produce': 'all_available',
            'bom_line_ids': [
                Command.create({
                    'product_id': cls.component_top.id,
                    'product_qty': 1.0,
                    'product_uom_id': cls.uom_unit.id,
                    'operation_id': cls.routing.operation_ids[0].id,
                    'sequence': 10,
                    'type': 'normal',
                    'mandatory': True,
                }),
                Command.create({
                    'product_id': cls.component_leg.id,
                    'product_qty': 4.0,
                    'product_uom_id': cls.uom_unit.id,
                    'operation_id': cls.routing.operation_ids[1].id,
                    'sequence': 20,
                    'type': 'normal',
                    'mandatory': True,
                }),
                Command.create({
                    'product_id': cls.component_screws.id,
                    'product_qty': 16.0,
                    'product_uom_id': cls.uom_unit.id,
                    'operation_id': cls.routing.operation_ids[1].id,
                    'sequence': 30,
                    'type': 'normal',
                    'mandatory': True,
                }),
            ],
            'byproduct_ids': [
                Command.create({
                    'product_id': cls.byproduct_scraps.id,
                    'product_qty': 0.5,
                    'product_uom_id': cls.uom_kg.id,
                    'operation_id': cls.routing.operation_ids[0].id,
                }),
            ],
        })

        cls.bom_phantom = cls.env['mrp.bom'].create({
            'product_id': cls.product_chair.id,
            'product_qty': 1.0,
            'uom_id': cls.uom_unit.id,
            'product_tmpl_id': cls.product_chair.product_tmpl_id.id,
            'type': 'phantom',
            'consumption': 'flexible',
            'ready_to_produce': 'asap',
            'bom_line_ids': [
                Command.create({
                    'product_id': cls.component_leg.id,
                    'product_qty': 4.0,
                    'product_uom_id': cls.uom_unit.id,
                    'sequence': 10,
                    'type': 'normal',
                    'mandatory': True,
                }),
            ],
        })

        # Create archived BOM
        cls.bom_archived = cls.env['mrp.bom'].create({
            'product_id': cls.product_chair.id,
            'product_qty': 1.0,
            'uom_id': cls.uom_unit.id,
            'product_tmpl_id': cls.product_chair.product_tmpl_id.id,
            'type': 'normal',
            'active': False,
        })

    # ==================== get_boms tests ====================

    def test_list_boms_returns_expected_fields(self):
        """List tool returns all required fields for each BOM."""
        result = get_boms(self.env, {})
        self.assertIn('boms', result)
        self.assertIn('total_count', result)
        self.assertIn('limit', result)
        self.assertIn('offset', result)

        if result['boms']:
            bom = result['boms'][0]
            required_fields = [
                'id', 'name', 'display_name', 'product_id', 'product_name',
                'type', 'company_id', 'company_name', 'version', 'active',
                'routing_id', 'routing_name', 'product_tmpl_id', 'product_tmpl_name'
            ]
            for field in required_fields:
                self.assertIn(field, bom, f"Missing field: {field}")

    def test_list_filter_by_type_normal(self):
        """Type filter works for normal BOMs."""
        result = get_boms(self.env, {'type': 'normal'})
        for bom in result['boms']:
            self.assertEqual(bom['type'], 'normal')

    def test_list_filter_by_type_phantom(self):
        """Type filter works for phantom BOMs."""
        result = get_boms(self.env, {'type': 'phantom'})
        for bom in result['boms']:
            self.assertEqual(bom['type'], 'phantom')

    def test_list_filter_by_type_subcontract(self):
        """Type filter works for subcontract BOMs."""
        result = get_boms(self.env, {'type': 'subcontract'})
        for bom in result['boms']:
            self.assertEqual(bom['type'], 'subcontract')

    def test_list_filter_by_product_id(self):
        """Product ID filter works correctly."""
        result = get_boms(self.env, {'product_id': self.product_table.id})
        for bom in result['boms']:
            self.assertEqual(bom['product_id'], self.product_table.id)

    def test_list_filter_by_product_tmpl_id(self):
        """Product template ID filter works correctly."""
        result = get_boms(self.env, {'product_tmpl_id': self.product_table.product_tmpl_id.id})
        for bom in result['boms']:
            self.assertEqual(bom['product_tmpl_id'], self.product_table.product_tmpl_id.id)

    def test_list_filter_by_company_id(self):
        """Company filter works correctly."""
        result = get_boms(self.env, {'company_id': self.env.company.id})
        for bom in result['boms']:
            self.assertEqual(bom['company_id'], self.env.company.id)

    def test_list_filter_active_true(self):
        """Active=true filter returns only active BOMs."""
        result = get_boms(self.env, {'active': True})
        for bom in result['boms']:
            self.assertTrue(bom['active'])

    def test_list_filter_active_false(self):
        """Active=false filter returns only archived BOMs."""
        result = get_boms(self.env, {'active': False})
        for bom in result['boms']:
            self.assertFalse(bom['active'])

    def test_list_pagination_limit(self):
        """Limit parameter respected."""
        result = get_boms(self.env, {'limit': 1})
        self.assertLessEqual(len(result['boms']), 1)
        self.assertEqual(result['limit'], 1)

    def test_list_pagination_offset(self):
        """Offset parameter works correctly."""
        all_boms = get_boms(self.env, {'limit': 10})['boms']
        if len(all_boms) > 1:
            first = get_boms(self.env, {'limit': 1, 'offset': 0})['boms']
            second = get_boms(self.env, {'limit': 1, 'offset': 1})['boms']
            self.assertNotEqual(first[0]['id'], second[0]['id'])

    def test_list_total_count_consistency(self):
        """Total count remains consistent across pages."""
        page1 = get_boms(self.env, {'limit': 1, 'offset': 0})
        page2 = get_boms(self.env, {'limit': 1, 'offset': 1})
        self.assertEqual(page1['total_count'], page2['total_count'])

    def test_list_empty_result(self):
        """Empty result handled correctly."""
        fake_product = self.env['product.product'].create({'name': 'Fake', 'type': 'consu'})
        result = get_boms(self.env, {'product_id': fake_product.id})
        self.assertEqual(result['boms'], [])
        self.assertEqual(result['total_count'], 0)

    def test_list_multiple_filters_combined(self):
        """Multiple filters work together."""
        result = get_boms(self.env, {
            'type': 'normal',
            'active': True,
            'company_id': self.env.company.id,
        })
        for bom in result['boms']:
            self.assertEqual(bom['type'], 'normal')
            self.assertTrue(bom['active'])
            self.assertEqual(bom['company_id'], self.env.company.id)

    def test_list_filter_by_product_name(self):
        """Product name filter works (case-insensitive partial match)."""
        result = get_boms(self.env, {'product_name': 'table'})
        for bom in result['boms']:
            self.assertIn('table', bom['product_name'].lower())

    def test_list_filter_by_product_code(self):
        """Product internal reference (default_code) filter works."""
        result = get_boms(self.env, {'product_code': 'TBL-001'})
        for bom in result['boms']:
            self.assertEqual(bom['product_name'], 'Wooden Table')

    def test_list_filter_by_product_name_no_results(self):
        """Product name filter with no matches returns empty."""
        result = get_boms(self.env, {'product_name': 'NonExistentProductXYZ'})
        self.assertEqual(result['boms'], [])
        self.assertEqual(result['total_count'], 0)

    def test_list_filter_by_product_code_no_results(self):
        """Product code filter with no matches returns empty."""
        result = get_boms(self.env, {'product_code': 'NONEXISTENT'})
        self.assertEqual(result['boms'], [])
        self.assertEqual(result['total_count'], 0)

    # ==================== get_bom tests ====================

    def test_detail_returns_all_sections(self):
        """Detail tool returns all required sections."""
        result = get_bom(self.env, {'bom_id': self.bom_normal.id})
        self.assertIn('bom', result)
        self.assertIn('bom_lines', result)
        self.assertIn('operations', result)
        self.assertIn('byproducts', result)

    def test_detail_bom_header_fields(self):
        """Detail BOM header contains all required fields."""
        result = get_bom(self.env, {'bom_id': self.bom_normal.id})
        bom = result['bom']
        required = [
            'id', 'name', 'display_name', 'product_id', 'product_name',
            'product_tmpl_id', 'product_tmpl_name', 'type', 'company_id',
            'company_name', 'version', 'active', 'routing_id', 'routing_name',
            'consumption', 'ready_to_produce', 'create_date', 'write_date'
        ]
        for field in required:
            self.assertIn(field, bom, f"Missing field: {field}")

    def test_detail_bom_header_values(self):
        """Detail BOM header has correct values."""
        result = get_bom(self.env, {'bom_id': self.bom_normal.id})
        bom = result['bom']
        self.assertEqual(bom['id'], self.bom_normal.id)
        self.assertEqual(bom['type'], 'normal')
        self.assertEqual(bom['consumption'], 'strict')
        self.assertEqual(bom['ready_to_produce'], 'all_available')
        self.assertIsNotNone(bom['routing_id'])
        self.assertIsNotNone(bom['create_date'])
        self.assertIsNotNone(bom['write_date'])

    def test_detail_bom_lines(self):
        """BOM lines returned with correct structure."""
        result = get_bom(self.env, {'bom_id': self.bom_normal.id})
        self.assertEqual(len(result['bom_lines']), 3)
        for line in result['bom_lines']:
            required = ['id', 'product_id', 'product_name', 'product_qty',
                        'product_uom_id', 'product_uom_name', 'sequence', 'type', 'mandatory']
            for field in required:
                self.assertIn(field, line)
            # Check operation_id is present for lines with operations
            self.assertIn('operation_id', line)
            self.assertIn('operation_name', line)

    def test_detail_bom_lines_values(self):
        """BOM lines have correct values."""
        result = get_bom(self.env, {'bom_id': self.bom_normal.id})
        lines_by_product = {l['product_name']: l for l in result['bom_lines']}
        self.assertEqual(lines_by_product['Table Top']['product_qty'], 1.0)
        self.assertEqual(lines_by_product['Table Leg']['product_qty'], 4.0)
        self.assertEqual(lines_by_product['Wood Screws']['product_qty'], 16.0)

    def test_detail_operations(self):
        """Operations returned with correct structure."""
        result = get_bom(self.env, {'bom_id': self.bom_normal.id})
        self.assertEqual(len(result['operations']), 2)
        for op in result['operations']:
            required = ['id', 'name', 'workcenter_id', 'workcenter_name',
                        'sequence', 'time_cycle', 'time_mode', 'workcenter_capacity']
            for field in required:
                self.assertIn(field, op)

    def test_detail_operations_values(self):
        """Operations have correct values."""
        result = get_bom(self.env, {'bom_id': self.bom_normal.id})
        ops_by_name = {o['name']: o for o in result['operations']}
        self.assertEqual(ops_by_name['Cutting']['workcenter_name'], 'CNC Machine 1')
        self.assertEqual(ops_by_name['Cutting']['time_mode'], 'auto')
        self.assertEqual(ops_by_name['Assembly']['workcenter_name'], 'Assembly Station 1')
        self.assertEqual(ops_by_name['Assembly']['time_mode'], 'manual')

    def test_detail_byproducts(self):
        """By-products returned with correct structure."""
        result = get_bom(self.env, {'bom_id': self.bom_normal.id})
        self.assertEqual(len(result['byproducts']), 1)
        bp = result['byproducts'][0]
        required = ['id', 'product_id', 'product_name', 'product_qty',
                    'product_uom_id', 'product_uom_name', 'operation_id', 'operation_name']
        for field in required:
            self.assertIn(field, bp)

    def test_detail_byproducts_values(self):
        """By-products have correct values."""
        result = get_bom(self.env, {'bom_id': self.bom_normal.id})
        bp = result['byproducts'][0]
        self.assertEqual(bp['product_name'], 'Wood Scraps')
        self.assertEqual(bp['product_qty'], 0.5)
        self.assertEqual(bp['product_uom_name'], 'kg')

    def test_detail_phantom_bom(self):
        """Phantom BOM returns correct type and no operations."""
        result = get_bom(self.env, {'bom_id': self.bom_phantom.id})
        self.assertEqual(result['bom']['type'], 'phantom')
        self.assertEqual(result['operations'], [])

    def test_detail_bom_without_routing(self):
        """BOM without routing returns empty operations."""
        result = get_bom(self.env, {'bom_id': self.bom_phantom.id})
        self.assertIsNone(result['bom']['routing_id'])
        self.assertIsNone(result['bom']['routing_name'])
        self.assertEqual(result['operations'], [])

    def test_detail_bom_without_lines(self):
        """BOM without component lines returns empty array."""
        empty_bom = self.env['mrp.bom'].create({
            'product_id': self.product_chair.id,
            'product_qty': 1.0,
            'uom_id': self.uom_unit.id,
            'product_tmpl_id': self.product_chair.product_tmpl_id.id,
            'type': 'normal',
        })
        result = get_bom(self.env, {'bom_id': empty_bom.id})
        self.assertEqual(result['bom_lines'], [])

    def test_detail_bom_without_byproducts(self):
        """BOM without by-products returns empty array."""
        result = get_bom(self.env, {'bom_id': self.bom_phantom.id})
        self.assertEqual(result['byproducts'], [])

    def test_detail_invalid_bom_id(self):
        """Invalid BOM ID returns clear error."""
        with self.assertRaises(ValueError) as cm:
            get_bom(self.env, {'bom_id': 99999})
        self.assertIn('not found', str(cm.exception))
        self.assertIn('99999', str(cm.exception))

    def test_detail_access_control(self):
        """Tool handles access control - users in same company may have access."""
        # In standard Odoo, users with mrp.group_mrp_user in the same company
        # can read all BOMs. This test verifies the tool doesn't crash.
        result = get_bom(self.env(user=self.user2), {'bom_id': self.bom_normal.id})
        self.assertEqual(result['bom']['id'], self.bom_normal.id)


@tagged('post_install', '-at_install', 'ai_chat_mcp')
class TestBomToolsPerformance(TransactionCase):
    """Performance tests for MCP BOM tools."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.group_user = cls.env.ref('mrp.group_mrp_user')
        cls.user = cls.env['res.users'].create({
            'name': 'BOM Perf Test', 'login': 'bom_perf_test',
            'group_ids': [Command.set([cls.group_user.id])],
            'company_id': cls.env.company.id,
        })
        cls.product = cls.env['product.product'].create({'name': 'Perf Product', 'type': 'consu'})
        cls.uom_unit = cls.env.ref('uom.product_uom_unit')
        cls.bom = cls.env['mrp.bom'].create({
            'product_id': cls.product.id,
            'product_qty': 1.0,
            'uom_id': cls.uom_unit.id,
            'product_tmpl_id': cls.product.product_tmpl_id.id,
        })
        # Create multiple BOMs for list performance test
        cls.boms = cls.env['mrp.bom'].create([
            {
                'product_id': cls.product.id,
                'product_qty': 1.0,
                'uom_id': cls.uom_unit.id,
                'product_tmpl_id': cls.product.product_tmpl_id.id,
                'type': 'normal',
            }
            for _ in range(50)
        ])

    def test_list_50_boms_under_2_seconds(self):
        """List 50 BOMs completes in under 2 seconds."""
        import time
        start = time.time()
        result = get_boms(self.env(user=self.user), {'limit': 50})
        elapsed = time.time() - start
        self.assertLess(elapsed, 2.0, f"List took {elapsed:.2f}s, expected < 2s")
        self.assertGreaterEqual(result['total_count'], 50)

    def test_detail_single_bom_under_3_seconds(self):
        """Single BOM detail completes in under 3 seconds."""
        import time
        start = time.time()
        result = get_bom(self.env(user=self.user), {'bom_id': self.bom.id})
        elapsed = time.time() - start
        self.assertLess(elapsed, 3.0, f"Detail took {elapsed:.2f}s, expected < 3s")
        self.assertEqual(result['bom']['id'], self.bom.id)
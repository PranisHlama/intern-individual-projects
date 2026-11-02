import logging
from typing import Any

from odoo.api import Environment

from ..registry import McpTool
from ..registry import McpToolRegistry


_logger = logging.getLogger(__name__)

VALID_BOM_TYPES = {
    'normal', 'phantom'
}

DEFAULT_LIMIT = 50
MAX_LIMIT = 200


def _build_bom_domain(
    env: Environment,
    product_id: int | None = None,
    product_tmpl_id: int | None = None,
    product_name: str | None = None,
    product_code: str | None = None,
    type: str | None = None,
    company_id: int | None = None,
    active: bool | None = None,
) -> list:
    """Build search domain for Bills of Materials."""
    domain = []

    if type:
        if type not in VALID_BOM_TYPES:
            raise ValueError(f"Invalid type: {type}. Valid types: {sorted(VALID_BOM_TYPES)}")
        domain.append(('type', '=', type))

    # Handle product_name and product_code by searching product.product first
    product_ids = []
    if product_name:
        if not isinstance(product_name, str):
            raise ValueError("product_name must be a string")
        products = env['product.product'].search([('name', 'ilike', product_name)])
        product_ids.extend(products.ids)

    if product_code:
        if not isinstance(product_code, str):
            raise ValueError("product_code must be a string")
        products = env['product.product'].search([('default_code', '=', product_code)])
        product_ids.extend(products.ids)

    if product_ids:
        domain.append(('product_id', 'in', product_ids))
    elif product_id:
        domain.append(('product_id', '=', product_id))

    if product_tmpl_id:
        domain.append(('product_tmpl_id', '=', product_tmpl_id))

    if company_id:
        domain.append(('company_id', '=', company_id))

    if active is not None:
        domain.append(('active', '=', active))

    return domain


def _format_bom(bom) -> dict[str, Any]:
    """Format BOM for list response."""
    # In Odoo 20, mrp.bom uses display_name as the primary identifier
    # (name field may not exist on this model)
    bom_name = bom.display_name
    # Some fields (routing_id, version) may not exist on mrp.bom
    # in all Odoo versions; use getattr to avoid AttributeError
    routing = getattr(bom, 'routing_id', None)
    version = getattr(bom, 'version', None)
    return {
        'id': bom.id,
        'name': bom_name,
        'display_name': bom.display_name,
        'product_id': bom.product_id.id if bom.product_id else None,
        'product_name': bom.product_id.display_name if bom.product_id else None,
        'product_tmpl_id': bom.product_tmpl_id.id if bom.product_tmpl_id else None,
        'product_tmpl_name': bom.product_tmpl_id.display_name if bom.product_tmpl_id else None,
        'type': bom.type,
        'company_id': bom.company_id.id if bom.company_id else None,
        'company_name': bom.company_id.name if bom.company_id else None,
        'version': version,
        'active': bom.active,
        'routing_id': routing.id if routing else None,
        'routing_name': routing.name if routing else None,
        'operation_count': bom.operation_count,
    }


def _format_bom_detail(bom) -> dict[str, Any]:
    """Format BOM for detail response with extended fields."""
    base = _format_bom(bom)
    # Some fields may not exist on mrp.bom in all Odoo versions
    base.update({
        'consumption': getattr(bom, 'consumption', None),
        'ready_to_produce': getattr(bom, 'ready_to_produce', None),
        'create_date': bom.create_date.isoformat() if getattr(bom, 'create_date', None) else None,
        'write_date': bom.write_date.isoformat() if getattr(bom, 'write_date', None) else None,
    })
    return base


def _format_bom_line(line) -> dict[str, Any]:
    """Format BOM line for detail response."""
    return {
        'id': line.id,
        'product_id': line.product_id.id if line.product_id else None,
        'product_name': line.product_id.display_name if line.product_id else None,
        'product_qty': getattr(line, 'product_qty', None),
        'product_uom_id': line.uom_id.id if line.uom_id else None,
        'product_uom_name': line.uom_id.name if line.uom_id else None,
        'operation_id': line.operation_id.id if line.operation_id else None,
        'operation_name': line.operation_id.name if line.operation_id else None,
        'sequence': getattr(line, 'sequence', None),
        'type': getattr(line, 'type', None),
        'mandatory': getattr(line, 'mandatory', None),
    }


def _format_operation(op) -> dict[str, Any]:
    """Format routing operation for detail response."""
    workcenter = getattr(op, 'workcenter_id', None)
    return {
        'id': op.id,
        'name': getattr(op, 'name', None),
        'workcenter_id': workcenter.id if workcenter else None,
        'workcenter_name': workcenter.name if workcenter else None,
        'sequence': getattr(op, 'sequence', None),
        'time_cycle': getattr(op, 'time_cycle', None),
        'time_mode': getattr(op, 'time_mode', None),
        'workcenter_capacity': workcenter.capacity if workcenter else None,
    }


def _format_byproduct(bp) -> dict[str, Any]:
    """Format by-product for detail response."""
    return {
        'id': bp.id,
        'product_id': bp.product_id.id if bp.product_id else None,
        'product_name': bp.product_id.display_name if bp.product_id else None,
        'product_qty': getattr(bp, 'product_qty', None),
        'product_uom_id': bp.uom_id.id if bp.uom_id else None,
        'product_uom_name': bp.uom_id.name if bp.uom_id else None,
        'operation_id': bp.operation_id.id if bp.operation_id else None,
        'operation_name': bp.operation_id.name if bp.operation_id else None,
    }


def get_boms(
    env: Environment,
    arguments: dict[str, Any],
) -> dict[str, Any]:
    """
    MCP tool: Retrieve list of Bills of Materials with filters.

    Returns structured list with pagination and total count.
    """
    # Validate and extract parameters
    product_id = arguments.get('product_id')
    product_tmpl_id = arguments.get('product_tmpl_id')
    product_name = arguments.get('product_name')
    product_code = arguments.get('product_code')
    type = arguments.get('type')
    company_id = arguments.get('company_id')
    active = arguments.get('active', True)
    limit = arguments.get('limit', DEFAULT_LIMIT)
    offset = arguments.get('offset', 0)

    # Validate limit
    if not isinstance(limit, int) or limit < 1:
        raise ValueError("limit must be a positive integer")
    if limit > MAX_LIMIT:
        raise ValueError(f"limit cannot exceed {MAX_LIMIT}")

    # Validate offset
    if not isinstance(offset, int) or offset < 0:
        raise ValueError("offset must be a non-negative integer")

    # Validate type
    if type is not None and not isinstance(type, str):
        raise ValueError("type must be a string")

    # Validate IDs
    for field, value in [('product_id', product_id), ('product_tmpl_id', product_tmpl_id), ('company_id', company_id)]:
        if value is not None and not isinstance(value, int):
            raise ValueError(f"{field} must be an integer")

    # Validate active
    if active is not None and not isinstance(active, bool):
        raise ValueError("active must be a boolean")

    # Build domain and search
    domain = _build_bom_domain(
        env, product_id, product_tmpl_id, product_name, product_code, type, company_id, active
    )

    Bom = env['mrp.bom']
    total_count = Bom.search_count(domain)
    boms = Bom.search(domain, limit=limit, offset=offset, order='id asc')

    _logger.info(
        "get_boms: filters=%s, returned=%d, total=%d",
        {k: v for k, v in arguments.items() if k not in ('limit', 'offset')},
        len(boms),
        total_count,
    )

    return {
        'boms': [_format_bom(b) for b in boms],
        'total_count': total_count,
        'limit': limit,
        'offset': offset,
    }


def get_bom(
    env: Environment,
    arguments: dict[str, Any],
) -> dict[str, Any]:
    """
    MCP tool: Retrieve full details for a single Bill of Materials.

    Returns BOM header, component lines, operations, and by-products.
    """
    bom_id = arguments.get('bom_id')

    if not isinstance(bom_id, int):
        raise ValueError("bom_id must be an integer")

    Bom = env['mrp.bom']
    bom = Bom.browse(bom_id)

    if not bom.exists():
        raise ValueError(f"Bill of Materials not found: {bom_id}")

    # Access control is automatic via env(user=...); if user lacks read access,
    # Odoo will raise AccessError when accessing fields

    # Fetch related records
    bom_lines = bom.bom_line_ids
    operations = bom.operation_ids
    byproducts = bom.byproduct_ids

    _logger.info(
        "get_bom: bom_id=%d, lines=%d, operations=%d, byproducts=%d",
        bom_id,
        len(bom_lines),
        len(operations),
        len(byproducts),
    )

    return {
        'bom': _format_bom_detail(bom),
        'bom_lines': [_format_bom_line(l) for l in bom_lines],
        'operations': [_format_operation(o) for o in operations],
        'byproducts': [_format_byproduct(b) for b in byproducts],
    }


def register_bom_tools(
    registry: McpToolRegistry,
) -> None:
    """Register BOM MCP tools."""

    registry.register(
        McpTool(
            name="get_boms",
            description=(
                "Retrieve a list of Bills of Materials with optional filters. "
                "Supports filtering by product, product template, product name, product code, "
                "BOM type, company, active status, and pagination. Returns key fields for each BOM."
            ),
            input_schema={
                "type": "object",
                "properties": {
                    "product_id": {
                        "type": "integer",
                        "description": "Filter by product variant ID (product.product)"
                    },
                    "product_tmpl_id": {
                        "type": "integer",
                        "description": "Filter by product template ID (product.template)"
                    },
                    "product_name": {
                        "type": "string",
                        "description": "Filter by product name (partial match, case-insensitive)"
                    },
                    "product_code": {
                        "type": "string",
                        "description": "Filter by product internal reference (default_code)"
                    },
                    "type": {
                        "type": "string",
                        "enum": sorted(VALID_BOM_TYPES),
                        "description": "Filter by BOM type: normal (manufacture), phantom (kit)"
                    },
                    "company_id": {
                        "type": "integer",
                        "description": "Filter by company ID"
                    },
                    "active": {
                        "type": "boolean",
                        "default": True,
                        "description": "Filter by active status (true = active, false = archived)"
                    },
                    "limit": {
                        "type": "integer",
                        "minimum": 1,
                        "maximum": MAX_LIMIT,
                        "default": DEFAULT_LIMIT,
                        "description": "Maximum number of BOMs to return"
                    },
                    "offset": {
                        "type": "integer",
                        "minimum": 0,
                        "default": 0,
                        "description": "Number of BOMs to skip (for pagination)"
                    }
                },
                "additionalProperties": False,
            },
            handler=get_boms,
        )
    )

    registry.register(
        McpTool(
            name="get_bom",
            description=(
                "Retrieve full details for a single Bill of Materials by ID. "
                "Returns BOM header, component lines (bom_lines), operations/routing, "
                "and by-products."
            ),
            input_schema={
                "type": "object",
                "properties": {
                    "bom_id": {
                        "type": "integer",
                        "description": "BOM ID (mrp.bom record ID)"
                    }
                },
                "required": ["bom_id"],
                "additionalProperties": False,
            },
            handler=get_bom,
        )
    )
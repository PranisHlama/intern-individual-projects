import logging
from typing import Any

from odoo.api import Environment

from ..registry import McpTool
from ..registry import McpToolRegistry


_logger = logging.getLogger(__name__)

DEFAULT_LIMIT = 50
MAX_LIMIT = 200


def _build_stock_quant_domain(
    env: Environment,
    product_id: int | None = None,
    product_tmpl_id: int | None = None,
    product_name: str | None = None,
    product_code: str | None = None,
    location_id: int | None = None,
    warehouse_id: int | None = None,
    company_id: int | None = None,
    only_internal: bool | None = None,
) -> list:
    """Build search domain for stock.quant records."""
    domain = []

    if product_id:
        domain.append(('product_id', '=', product_id))

    if product_tmpl_id:
        domain.append(('product_tmpl_id', '=', product_tmpl_id))

    if product_name:
        if not isinstance(product_name, str):
            raise ValueError("product_name must be a string")
        products = env['product.product'].search([('name', 'ilike', product_name)])
        if products:
            domain.append(('product_id', 'in', products.ids))
        else:
            domain.append(('product_id', '=', 0))

    if product_code:
        if not isinstance(product_code, str):
            raise ValueError("product_code must be a string")
        products = env['product.product'].search([('default_code', '=', product_code)])
        if products:
            domain.append(('product_id', 'in', products.ids))
        else:
            domain.append(('product_id', '=', 0))

    if location_id:
        domain.append(('location_id', '=', location_id))

    if warehouse_id:
        domain.append(('warehouse_id', '=', warehouse_id))

    if company_id:
        domain.append(('company_id', '=', company_id))

    if only_internal is not None:
        if not isinstance(only_internal, bool):
            raise ValueError("only_internal must be a boolean")
        if only_internal:
            domain.append(('location_id.usage', '=', 'internal'))

    return domain


def _format_stock_quant(quant) -> dict[str, Any]:
    """Format a stock.quant record for list response."""
    product = quant.product_id
    location = quant.location_id
    uom = quant.uom_id
    warehouse = quant.warehouse_id
    lot = quant.lot_id

    return {
        'id': quant.id,
        'product_id': product.id if product else None,
        'product_name': product.display_name if product else None,
        'product_code': product.default_code if product else None,
        'product_tmpl_id': quant.product_tmpl_id.id if quant.product_tmpl_id else None,
        'product_tmpl_name': quant.product_tmpl_id.display_name if quant.product_tmpl_id else None,
        'location_id': location.id if location else None,
        'location_name': location.display_name if location else None,
        'location_usage': location.usage if location else None,
        'warehouse_id': warehouse.id if warehouse else None,
        'warehouse_name': warehouse.name if warehouse else None,
        'company_id': quant.company_id.id if quant.company_id else None,
        'company_name': quant.company_id.name if quant.company_id else None,
        'quantity': quant.quantity,
        'reserved_quantity': quant.reserved_quantity,
        'available_quantity': quant.available_quantity,
        'uom_id': uom.id if uom else None,
        'uom_name': uom.name if uom else None,
        'lot_id': lot.id if lot else None,
        'lot_name': lot.display_name if lot else None,
        'on_hand': quant.on_hand,
        'tracking': quant.tracking,
    }


def _format_product_stock(product) -> dict[str, Any]:
    """Format a product.product record with computed stock fields."""
    uom = product.uom_id
    categ = product.categ_id

    return {
        'id': product.id,
        'name': product.display_name,
        'product_code': product.default_code,
        'type': product.type,
        'qty_available': product.qty_available,
        'virtual_available': product.virtual_available,
        'incoming_qty': product.incoming_qty,
        'outgoing_qty': product.outgoing_qty,
        'free_qty': product.free_qty,
        'mrp_product_qty': product.mrp_product_qty,
        'uom_id': uom.id if uom else None,
        'uom_name': uom.name if uom else None,
        'category_id': categ.id if categ else None,
        'category_name': categ.name if categ else None,
    }


def get_stock_levels(
    env: Environment,
    arguments: dict[str, Any],
) -> dict[str, Any]:
    """
    MCP tool: Retrieve current stock levels (quantities on hand) across products
    and locations.

    Returns structured list with pagination and total count. Each item includes
    product, location, warehouse, quantity on hand, reserved quantity, and unit
    of measure.
    """
    # Validate and extract parameters
    product_id = arguments.get('product_id')
    product_tmpl_id = arguments.get('product_tmpl_id')
    product_name = arguments.get('product_name')
    product_code = arguments.get('product_code')
    location_id = arguments.get('location_id')
    warehouse_id = arguments.get('warehouse_id')
    company_id = arguments.get('company_id')
    only_internal = arguments.get('only_internal', False)
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

    # Validate IDs
    for field, value in [('product_id', product_id), ('product_tmpl_id', product_tmpl_id),
                          ('location_id', location_id), ('warehouse_id', warehouse_id),
                          ('company_id', company_id)]:
        if value is not None and not isinstance(value, int):
            raise ValueError(f"{field} must be an integer")

    # Validate only_internal
    if only_internal is not None and not isinstance(only_internal, bool):
        raise ValueError("only_internal must be a boolean")

    # Build domain and search
    domain = _build_stock_quant_domain(
        env, product_id, product_tmpl_id, product_name, product_code,
        location_id, warehouse_id, company_id, only_internal,
    )

    Quant = env['stock.quant']
    total_count = Quant.search_count(domain)
    quants = Quant.search(domain, limit=limit, offset=offset, order='id asc')

    _logger.info(
        "get_stock_levels: filters=%s, returned=%d, total=%d",
        {k: v for k, v in arguments.items() if k not in ('limit', 'offset')},
        len(quants),
        total_count,
    )

    return {
        'quant': [_format_stock_quant(q) for q in quants],
        'total_count': total_count,
        'limit': limit,
        'offset': offset,
    }


def get_product_stock(
    env: Environment,
    arguments: dict[str, Any],
) -> dict[str, Any]:
    """
    MCP tool: Retrieve stock summary for products using computed fields.

    Returns quantity on hand, forecasted quantity, incoming, outgoing, and free
    quantity for each matching product.
    """
    # Validate and extract parameters
    product_id = arguments.get('product_id')
    product_name = arguments.get('product_name')
    product_code = arguments.get('product_code')
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

    # Validate IDs
    if product_id is not None and not isinstance(product_id, int):
        raise ValueError("product_id must be an integer")

    # Build domain
    domain = []
    if product_id:
        domain.append(('id', '=', product_id))

    if product_name:
        if not isinstance(product_name, str):
            raise ValueError("product_name must be a string")
        domain.append(('name', 'ilike', product_name))

    if product_code:
        if not isinstance(product_code, str):
            raise ValueError("product_code must be a string")
        domain.append(('default_code', '=', product_code))

    # Only stockable products
    domain.append(('type', 'in', ['product', 'consu']))

    Product = env['product.product']
    total_count = Product.search_count(domain)
    products = Product.search(domain, limit=limit, offset=offset, order='id asc')

    _logger.info(
        "get_product_stock: filters=%s, returned=%d, total=%d",
        {k: v for k, v in arguments.items() if k not in ('limit', 'offset')},
        len(products),
        total_count,
    )

    return {
        'products': [_format_product_stock(p) for p in products],
        'total_count': total_count,
        'limit': limit,
        'offset': offset,
    }


def register_inventory_tools(
    registry: McpToolRegistry,
) -> None:
    """Register inventory MCP tools."""

    registry.register(
        McpTool(
            name="get_stock_levels",
            description=(
                "Retrieve current stock levels (quantities on hand) across "
                "products and locations. Supports filtering by product, product "
                "template, product name, product code, location, warehouse, "
                "company, and internal-only locations. Returns quantity on hand, "
                "reserved quantity, available quantity, and unit of measure."
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
                    "location_id": {
                        "type": "integer",
                        "description": "Filter by stock location ID"
                    },
                    "warehouse_id": {
                        "type": "integer",
                        "description": "Filter by warehouse ID"
                    },
                    "company_id": {
                        "type": "integer",
                        "description": "Filter by company ID"
                    },
                    "only_internal": {
                        "type": "boolean",
                        "default": False,
                        "description": "Filter to internal storage locations only"
                    },
                    "limit": {
                        "type": "integer",
                        "minimum": 1,
                        "maximum": MAX_LIMIT,
                        "default": DEFAULT_LIMIT,
                        "description": "Maximum number of records to return"
                    },
                    "offset": {
                        "type": "integer",
                        "minimum": 0,
                        "default": 0,
                        "description": "Number of records to skip (for pagination)"
                    }
                },
                "additionalProperties": False,
            },
            handler=get_stock_levels,
        )
    )

    registry.register(
        McpTool(
            name="get_product_stock",
            description=(
                "Retrieve stock summary for products using computed fields. "
                "Returns quantity on hand, forecasted quantity, incoming, "
                "outgoing, and free quantity for each matching product. "
                "Supports filtering by product ID, name, or internal reference."
            ),
            input_schema={
                "type": "object",
                "properties": {
                    "product_id": {
                        "type": "integer",
                        "description": "Filter by product variant ID (product.product)"
                    },
                    "product_name": {
                        "type": "string",
                        "description": "Filter by product name (partial match, case-insensitive)"
                    },
                    "product_code": {
                        "type": "string",
                        "description": "Filter by product internal reference (default_code)"
                    },
                    "limit": {
                        "type": "integer",
                        "minimum": 1,
                        "maximum": MAX_LIMIT,
                        "default": DEFAULT_LIMIT,
                        "description": "Maximum number of products to return"
                    },
                    "offset": {
                        "type": "integer",
                        "minimum": 0,
                        "default": 0,
                        "description": "Number of products to skip (for pagination)"
                    }
                },
                "additionalProperties": False,
            },
            handler=get_product_stock,
        )
    )
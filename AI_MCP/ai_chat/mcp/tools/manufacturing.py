import logging
from typing import Any

from odoo.api import Environment
from odoo.exceptions import AccessError
from odoo.tools import date_utils

from ..registry import McpTool
from ..registry import McpToolRegistry


_logger = logging.getLogger(__name__)

VALID_STATES = {
    'draft', 'confirmed', 'progress', 'to_close', 'done', 'cancel'
}

DEFAULT_LIMIT = 50
MAX_LIMIT = 200


def _build_order_domain(
    env: Environment,
    state: str | None = None,
    product_id: int | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
    user_id: int | None = None,
    include_archived: bool = False,
) -> list:
    """Build search domain for manufacturing orders."""
    domain = []

    # Note: mrp.production does not have an 'active' field in Odoo 20
    # Archived orders are handled differently

    if state:
        if state not in VALID_STATES:
            raise ValueError(f"Invalid state: {state}. Valid states: {sorted(VALID_STATES)}")
        domain.append(('state', '=', state))

    if product_id:
        domain.append(('product_id', '=', product_id))

    if date_from:
        domain.append(('date_deadline', '>=', date_from))

    if date_to:
        domain.append(('date_deadline', '<=', date_to))

    if user_id:
        domain.append(('user_id', '=', user_id))

    return domain


def _format_order(order) -> dict[str, Any]:
    """Format manufacturing order for list response."""
    return {
        'id': order.id,
        'name': order.name,
        'state': order.state,
        'product_id': order.product_id.id,
        'product_name': order.product_id.display_name,
        'product_qty': order.product_qty,
        'qty_produced': order.qty_produced,
        'date_planned_start': order.date_deadline.isoformat() if order.date_deadline else None,
        'date_planned_finished': order.date_deadline.isoformat() if order.date_deadline else None,
        'user_id': order.user_id.id if order.user_id else None,
        'user_name': order.user_id.name if order.user_id else None,
        'bom_id': order.bom_id.id if order.bom_id else None,
        'bom_name': order.bom_id.display_name if order.bom_id else None,
        'company_id': order.company_id.id if order.company_id else None,
    }


def _format_bom_line(line) -> dict[str, Any]:
    """Format BOM line for detail response."""
    return {
        'id': line.id,
        'product_id': line.product_id.id,
        'product_name': line.product_id.display_name,
        'product_qty': line.product_qty,
        'product_uom_id': line.uom_id.id if line.uom_id else None,
        'product_uom_name': line.uom_id.name if line.uom_id else None,
        'qty_consumed': 0.0,  # Will be updated from stock moves if needed
    }


def _format_work_order(wo) -> dict[str, Any]:
    """Format work order for detail response."""
    return {
        'id': wo.id,
        'name': wo.name,
        'operation_id': wo.operation_id.id if wo.operation_id else None,
        'operation_name': wo.operation_id.name if wo.operation_id else None,
        'workcenter_id': wo.workcenter_id.id if wo.workcenter_id else None,
        'workcenter_name': wo.workcenter_id.name if wo.workcenter_id else None,
        'state': wo.state,
        'duration_expected': wo.duration_expected,
        'duration': wo.duration,
        'date_planned_start': wo.date_planned_start.isoformat() if wo.date_planned_start else None,
        'date_planned_finished': wo.date_planned_finished.isoformat() if wo.date_planned_finished else None,
        'date_start': wo.date_start.isoformat() if wo.date_start else None,
        'date_finished': wo.date_finished.isoformat() if wo.date_finished else None,
    }


def _format_stock_move(move) -> dict[str, Any]:
    """Format stock move for detail response."""
    return {
        'id': move.id,
        'name': move.display_name or move.reference,
        'product_id': move.product_id.id,
        'product_name': move.product_id.display_name,
        'product_qty': move.product_qty,
        'product_uom_qty': move.product_uom_qty,
        'product_uom_id': move.uom_id.id if move.uom_id else None,
        'location_id': move.location_id.id if move.location_id else None,
        'location_name': move.location_id.display_name if move.location_id else None,
        'location_dest_id': move.location_dest_id.id if move.location_dest_id else None,
        'location_dest_name': move.location_dest_id.display_name if move.location_dest_id else None,
        'state': move.state,
    }


def _format_scrap(scrap) -> dict[str, Any]:
    """Format scrap record for detail response."""
    return {
        'id': scrap.id,
        'product_id': scrap.product_id.id,
        'product_name': scrap.product_id.display_name,
        'scrap_qty': scrap.scrap_qty,
        'product_uom_id': scrap.product_uom_id.id if scrap.product_uom_id else None,
        'location_id': scrap.location_id.id if scrap.location_id else None,
        'location_name': scrap.location_id.display_name if scrap.location_id else None,
        'date_done': scrap.date_done.isoformat() if scrap.date_done else None,
    }


def get_manufacturing_orders(
    env: Environment,
    arguments: dict[str, Any],
) -> dict[str, Any]:
    """
    MCP tool: Retrieve list of manufacturing orders with filters.

    Returns structured list with pagination and total count.
    """
    # Validate and extract parameters
    state = arguments.get('state')
    product_id = arguments.get('product_id')
    date_from = arguments.get('date_from')
    date_to = arguments.get('date_to')
    user_id = arguments.get('user_id')
    limit = arguments.get('limit', DEFAULT_LIMIT)
    offset = arguments.get('offset', 0)
    include_archived = arguments.get('include_archived', False)

    # Validate limit
    if not isinstance(limit, int) or limit < 1:
        raise ValueError("limit must be a positive integer")
    if limit > MAX_LIMIT:
        raise ValueError(f"limit cannot exceed {MAX_LIMIT}")

    # Validate offset
    if not isinstance(offset, int) or offset < 0:
        raise ValueError("offset must be a non-negative integer")

    # Build domain and search
    domain = _build_order_domain(
        env, state, product_id, date_from, date_to, user_id, include_archived
    )

    Production = env['mrp.production']
    total_count = Production.search_count(domain)
    orders = Production.search(domain, limit=limit, offset=offset, order='date_deadline desc, id desc')

    return {
        'orders': [_format_order(o) for o in orders],
        'total_count': total_count,
        'limit': limit,
        'offset': offset,
    }


def get_manufacturing_order(
    env: Environment,
    arguments: dict[str, Any],
) -> dict[str, Any]:
    """
    MCP tool: Retrieve full details for a single manufacturing order.

    Returns order header, BOM lines, work orders, stock moves, and scrap records.
    """
    order_id = arguments.get('order_id')

    if not isinstance(order_id, int):
        raise ValueError("order_id must be an integer")

    Production = env['mrp.production']
    order = Production.browse(order_id)

    if not order.exists():
        raise ValueError(f"Manufacturing order not found: {order_id}")

    # Access control is automatic via env(user=...); if user lacks read access,
    # Odoo will raise AccessError when accessing fields

    # Fetch related records
    bom_lines = order.bom_id.bom_line_ids if order.bom_id else env['mrp.bom.line']
    work_orders = env['mrp.workorder'].search([('production_id', '=', order.id)])
    stock_moves = env['stock.move'].search([('raw_material_production_id', '=', order.id)])
    # Also include finished product moves
    finished_moves = env['stock.move'].search([('production_id', '=', order.id)])
    stock_moves = stock_moves | finished_moves
    # stock.scrap may not be installed in all Odoo configurations
    scrap_records = env.registry.get('stock.scrap')
    if scrap_records:
        scrap_records = env['stock.scrap'].search([('production_id', '=', order.id)])
    else:
        scrap_records = []

    # Format response
    order_data = {
        'id': order.id,
        'name': order.name,
        'state': order.state,
        'product_id': order.product_id.id,
        'product_name': order.product_id.display_name,
        'product_qty': order.product_qty,
        'product_uom_id': order.uom_id.id if order.uom_id else None,
        'product_uom_name': order.uom_id.name if order.uom_id else None,
        'qty_produced': order.qty_produced,
        'qty_producing': order.qty_producing,
        'date_planned_start': order.date_deadline.isoformat() if order.date_deadline else None,
        'date_planned_finished': order.date_deadline.isoformat() if order.date_deadline else None,
        'date_start': order.date_start.isoformat() if order.date_start else None,
        'date_finished': order.date_finished.isoformat() if order.date_finished else None,
        'user_id': order.user_id.id if order.user_id else None,
        'user_name': order.user_id.name if order.user_id else None,
        'bom_id': order.bom_id.id if order.bom_id else None,
        'bom_name': order.bom_id.display_name if order.bom_id else None,
        'company_id': order.company_id.id if order.company_id else None,
        'origin': order.origin,
        'notes': order.note,
    }

    return {
        'order': order_data,
        'bom_lines': [_format_bom_line(l) for l in bom_lines],
        'work_orders': [_format_work_order(wo) for wo in work_orders],
        'stock_moves': [_format_stock_move(m) for m in stock_moves],
        'scrap_records': [_format_scrap(s) for s in scrap_records],
    }


def register_manufacturing_tools(
    registry: McpToolRegistry,
) -> None:
    """Register manufacturing order MCP tools."""

    registry.register(
        McpTool(
            name="get_manufacturing_orders",
            description=(
                "Retrieve a list of manufacturing orders with optional filters. "
                "Supports filtering by state, product, date range, responsible user, "
                "and pagination. Returns key fields for each order."
            ),
            input_schema={
                "type": "object",
                "properties": {
                    "state": {
                        "type": "string",
                        "enum": sorted(VALID_STATES),
                        "description": "Filter by manufacturing order state"
                    },
                    "product_id": {
                        "type": "integer",
                        "description": "Filter by product ID"
                    },
                    "date_from": {
                        "type": "string",
                        "format": "date",
                        "description": "Filter orders with scheduled date >= this date (date_planned_start)"
                    },
                    "date_to": {
                        "type": "string",
                        "format": "date",
                        "description": "Filter orders with scheduled date <= this date (date_planned_start)"
                    },
                    "user_id": {
                        "type": "integer",
                        "description": "Filter by responsible user ID"
                    },
                    "limit": {
                        "type": "integer",
                        "minimum": 1,
                        "maximum": MAX_LIMIT,
                        "default": DEFAULT_LIMIT,
                        "description": "Maximum number of orders to return"
                    },
                    "offset": {
                        "type": "integer",
                        "minimum": 0,
                        "default": 0,
                        "description": "Number of orders to skip (for pagination)"
                    },
                    "include_archived": {
                        "type": "boolean",
                        "default": False,
                        "description": "Include archived (inactive) orders"
                    }
                },
                "additionalProperties": False,
            },
            handler=get_manufacturing_orders,
        )
    )

    registry.register(
        McpTool(
            name="get_manufacturing_order",
            description=(
                "Retrieve full details for a single manufacturing order by ID. "
                "Returns order header, BOM lines (components), work orders with operations, "
                "stock moves, and scrap records."
            ),
            input_schema={
                "type": "object",
                "properties": {
                    "order_id": {
                        "type": "integer",
                        "description": "Manufacturing order ID (mrp.production record ID)"
                    }
                },
                "required": ["order_id"],
                "additionalProperties": False,
            },
            handler=get_manufacturing_order,
        )
    )
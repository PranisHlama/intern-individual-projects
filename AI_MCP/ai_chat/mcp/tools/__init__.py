from .knowledge import register_knowledge_tools
from .manufacturing import register_manufacturing_tools
from .system import register_system_tools
from .bom import register_bom_tools
from .inventory import register_inventory_tools


def register_all_tools(
    registry,
) -> None:

    register_system_tools(
        registry,
    )

    register_knowledge_tools(
        registry,
    )

    register_manufacturing_tools(
        registry,
    )

    register_bom_tools(
        registry,
    )

    register_inventory_tools(
        registry,
    )

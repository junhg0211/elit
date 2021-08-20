class CapacityError(Exception):
    """섬 인원수 초과"""


class InventoryCapacityError(Exception):
    """인벤토리 용량 초과"""


class ChannelError(Exception):
    """올바르지 않은 채널"""


class CropCapacityError(Exception):
    """섬 작물 개수 초과"""

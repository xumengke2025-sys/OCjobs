"""
API路由模块
"""

from flask import Blueprint

fortune_bp = Blueprint('fortune', __name__)
recruit_bp = Blueprint('recruit', __name__)

from . import fortune  # noqa: E402, F401
from . import recruit  # noqa: E402, F401

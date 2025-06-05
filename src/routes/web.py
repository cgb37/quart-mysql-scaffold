"""
Web routes for serving HTML pages.
"""
from quart import Blueprint, render_template, request, redirect, url_for

from src.services.logging_service import get_logger

web_bp = Blueprint('web', __name__)
logger = get_logger(__name__)


@web_bp.route('/')
async def index():
    """Home page."""
    return await render_template('index.html')


@web_bp.route('/login')
async def login_page():
    """Login page."""
    return await render_template('auth/login.html')


@web_bp.route('/register')
async def register_page():
    """Registration page."""
    return await render_template('auth/register.html')


@web_bp.route('/dashboard')
async def dashboard():
    """Dashboard page (requires authentication)."""
    # In a real app, you'd check authentication here
    return await render_template('dashboard.html')


@web_bp.route('/docs')
async def api_docs():
    """API documentation page."""
    return await render_template('docs.html')


@web_bp.route('/favicon.ico')
async def favicon():
    """Favicon handler."""
    return '', 204  # No content
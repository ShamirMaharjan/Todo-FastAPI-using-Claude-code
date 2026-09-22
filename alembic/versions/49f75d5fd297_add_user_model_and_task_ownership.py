"""add_user_model_and_task_ownership

Revision ID: 49f75d5fd297
Revises: c8e51e8ff3b4
Create Date: 2026-09-17 10:38:44.534200

"""
from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = '49f75d5fd297'
down_revision: Union[str, Sequence[str], None] = 'c8e51e8ff3b4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """No-op: users table and task ownership are created in the initial migration."""
    pass


def downgrade() -> None:
    """No-op."""
    pass

"""Add user model and task ownership.

Revision ID: 49f75d5fd297
Revises: c8e51e8ff3b4
Create Date: 2026-09-17 10:38:44.534200

"""

# revision identifiers, used by Alembic.
revision: str = "49f75d5fd297"
down_revision: str | list[str] | None = "c8e51e8ff3b4"
branch_labels: str | list[str] | None = None
depends_on: str | list[str] | None = None


def upgrade() -> None:
    """No-op: users table and task ownership are created in the initial migration."""
    pass


def downgrade() -> None:
    """No-op."""
    pass

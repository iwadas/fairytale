"""Add Music table

Revision ID: de3d6f66c6fa
Revises: 7770d066dcde
Create Date: 2026-02-25 20:10:21.274351

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'de3d6f66c6fa'
down_revision: Union[str, Sequence[str], None] = '7770d066dcde'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Use batch mode for SQLite compatibility
    with op.batch_alter_table('projects', schema=None) as batch_op:
        batch_op.drop_constraint('fk_projects_images_package', type_='foreignkey')
        batch_op.drop_column('images_package_id')

def downgrade() -> None:
    """Downgrade schema."""
    # Use batch mode for SQLite compatibility
    with op.batch_alter_table('projects', schema=None) as batch_op:
        batch_op.add_column(sa.Column('images_package_id', sa.VARCHAR(length=36), nullable=True))
        batch_op.create_foreign_key('fk_projects_images_package', 'images_packages', ['images_package_id'], ['id'])
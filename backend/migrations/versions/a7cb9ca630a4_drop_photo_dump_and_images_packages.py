"""Drop photo dump and images packages tables

Removes the photo-dump / images-package feature:
project_images_package_association, photo_dump_images, images_packages.
(projects.images_package_id was already dropped in de3d6f66c6fa.)

Revision ID: a7cb9ca630a4
Revises: fa950cd327c8
Create Date: 2026-11-09 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a7cb9ca630a4'
down_revision: Union[str, Sequence[str], None] = 'fa950cd327c8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.drop_table('project_images_package_association')
    op.drop_index(op.f('ix_photo_dump_images_package_id'), table_name='photo_dump_images')
    op.drop_table('photo_dump_images')
    op.drop_table('images_packages')


def downgrade() -> None:
    """Downgrade schema."""
    op.create_table('images_packages',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_table('photo_dump_images',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('package_id', sa.String(length=36), nullable=False),
        sa.Column('prompt', sa.Text(), nullable=True),
        sa.Column('src', sa.String(), nullable=True),
        sa.ForeignKeyConstraint(['package_id'], ['images_packages.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_photo_dump_images_package_id'), 'photo_dump_images', ['package_id'], unique=False)
    op.create_table('project_images_package_association',
        sa.Column('project_id', sa.String(length=36), nullable=True),
        sa.Column('images_package_id', sa.String(length=36), nullable=True),
        sa.ForeignKeyConstraint(['images_package_id'], ['images_packages.id'], ),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], )
    )

"""
init

Revision ID: 0001_init
Revises: 
Create Date: 2025-08-10 00:00:00.000000
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '0001_init'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'users',
        sa.Column('id', sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column('email', sa.String(length=255), nullable=False, unique=True),
        sa.Column('password_hash', sa.String(length=255), nullable=False),
        sa.Column('created_at', sa.TIMESTAMP(), server_default=sa.func.current_timestamp(), nullable=False),
        sa.Column('flags_json', sa.JSON(), nullable=True),
        mysql_charset='utf8mb4',
        mysql_collate='utf8mb4_0900_ai_ci',
    )
    op.create_index('ix_users_email', 'users', ['email'], unique=True)

    op.create_table(
        'characters',
        sa.Column('id', sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column('user_id', sa.BigInteger(), sa.ForeignKey('users.id', ondelete='RESTRICT'), nullable=False),
        sa.Column('name', sa.String(length=32), nullable=False),
        sa.Column('class', sa.String(length=32), nullable=False, server_default='adventurer'),
        sa.Column('level', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('xp', sa.BigInteger(), nullable=False, server_default='0'),
        sa.Column('map', sa.String(length=64), nullable=False, server_default='start'),
        sa.Column('x', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('y', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('hp', sa.Integer(), nullable=False, server_default='100'),
        sa.Column('mp', sa.Integer(), nullable=False, server_default='50'),
        sa.Column('attrs_json', sa.JSON(), nullable=True),
        sa.Column('last_login_at', sa.TIMESTAMP(), nullable=True),
        sa.Column('updated_at', sa.TIMESTAMP(), server_default=sa.func.current_timestamp(), onupdate=sa.func.current_timestamp(), nullable=False),
        mysql_charset='utf8mb4',
        mysql_collate='utf8mb4_0900_ai_ci',
    )
    op.create_index('ix_characters_user_id', 'characters', ['user_id'])
    op.create_index('ix_characters_name_user', 'characters', ['user_id', 'name'], unique=False)


def downgrade() -> None:
    op.drop_index('ix_characters_name_user', table_name='characters')
    op.drop_index('ix_characters_user_id', table_name='characters')
    op.drop_table('characters')
    op.drop_index('ix_users_email', table_name='users')
    op.drop_table('users')




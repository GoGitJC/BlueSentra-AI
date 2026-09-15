"""Normalized network events and Zeek conn import support

Revision ID: 20260314_0002
Revises: 20260314_0001
Create Date: 2026-03-14

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "20260314_0002"
down_revision: Union[str, Sequence[str], None] = "20260314_0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_unique_constraint(
        "uq_sensors_id_site_msp",
        "sensors",
        ["id", "site_id", "msp_id"],
    )
    op.create_unique_constraint(
        "uq_devices_id_msp_site",
        "devices",
        ["id", "msp_id", "site_id"],
    )

    op.create_table(
        "network_events",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("msp_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("site_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("sensor_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("device_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column(
            "source_type",
            sa.Enum("zeek_conn", name="network_event_source_type", native_enum=False),
            nullable=False,
        ),
        sa.Column("source_event_id", sa.String(length=128), nullable=False),
        sa.Column("event_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column(
            "ingested_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("src_ip", sa.String(length=45), nullable=False),
        sa.Column("dst_ip", sa.String(length=45), nullable=False),
        sa.Column("src_port", sa.Integer(), nullable=True),
        sa.Column("dst_port", sa.Integer(), nullable=True),
        sa.Column("transport_protocol", sa.String(length=16), nullable=False),
        sa.Column("service", sa.String(length=64), nullable=True),
        sa.Column("duration", sa.Float(), nullable=True),
        sa.Column("orig_bytes", sa.Integer(), nullable=True),
        sa.Column("resp_bytes", sa.Integer(), nullable=True),
        sa.Column("orig_pkts", sa.Integer(), nullable=True),
        sa.Column("resp_pkts", sa.Integer(), nullable=True),
        sa.Column("source_record", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.ForeignKeyConstraint(["device_id"], ["devices.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["msp_id"], ["msps.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["sensor_id"], ["sensors.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["site_id"], ["sites.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(
            ["site_id", "msp_id"],
            ["sites.id", "sites.msp_id"],
            name="fk_network_events_site_msp",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["sensor_id", "site_id", "msp_id"],
            ["sensors.id", "sensors.site_id", "sensors.msp_id"],
            name="fk_network_events_sensor_site_msp",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["device_id", "msp_id", "site_id"],
            ["devices.id", "devices.msp_id", "devices.site_id"],
            name="fk_network_events_device_site_msp",
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("id", "msp_id", name="uq_network_events_id_msp"),
        sa.UniqueConstraint(
            "sensor_id",
            "source_type",
            "source_event_id",
            name="uq_network_events_sensor_source",
        ),
    )
    op.create_index(
        "ix_network_events_msp_site_event_at",
        "network_events",
        ["msp_id", "site_id", "event_at"],
        unique=False,
    )
    op.create_index(
        "ix_network_events_sensor_event_at",
        "network_events",
        ["sensor_id", "event_at"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_network_events_sensor_event_at", table_name="network_events")
    op.drop_index("ix_network_events_msp_site_event_at", table_name="network_events")
    op.drop_table("network_events")
    op.drop_constraint("uq_devices_id_msp_site", "devices", type_="unique")
    op.drop_constraint("uq_sensors_id_site_msp", "sensors", type_="unique")

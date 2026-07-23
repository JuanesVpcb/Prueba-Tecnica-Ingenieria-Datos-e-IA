from __future__ import annotations

from datetime import date

from pydantic import BaseModel, Field, field_validator

from src.data.models import ChannelEnum


CHANNEL_MAPPING = {
    "fb ads": ChannelEnum.FACEBOOK,
    "facebook_ads": ChannelEnum.FACEBOOK,
    "facebook": ChannelEnum.FACEBOOK,
    "facebook ads": ChannelEnum.FACEBOOK,
    "fb": ChannelEnum.FACEBOOK,
    "instagram_ads": ChannelEnum.INSTAGRAM,
    "instagram": ChannelEnum.INSTAGRAM,
    "insta": ChannelEnum.INSTAGRAM,
    "ig": ChannelEnum.INSTAGRAM,
    "tiktok": ChannelEnum.TIKTOK,
    "tt": ChannelEnum.TIKTOK,
    "email": ChannelEnum.EMAIL,
    "mail": ChannelEnum.EMAIL,
    "web": ChannelEnum.WEB,
    "website": ChannelEnum.WEB,
    "google": ChannelEnum.WEB,
    "google_ads": ChannelEnum.WEB,
    "google adwords": ChannelEnum.WEB,
    "radio": ChannelEnum.RADIO,
    "feria": ChannelEnum.FERIA,
    "fair": ChannelEnum.FERIA,
    "directo": ChannelEnum.DIRECT,
    "direct": ChannelEnum.DIRECT,
    "dm": ChannelEnum.DIRECT,
}


def normalize_channel(channel: str) -> ChannelEnum:
    normalized = channel.strip().lower()
    return CHANNEL_MAPPING.get(normalized, ChannelEnum.OTHER)


class RecordCosto(BaseModel):
    fecha: date
    canal_venta: str
    costo: int
    impresiones: int
    clicks: int
    nuevos_usuarios: int

    @field_validator("costo", "impresiones", "clicks", "nuevos_usuarios")
    @classmethod
    def amount_must_be_non_negative(cls, value: int) -> int:
        if value < 0:
            raise ValueError("La cantidad debe ser un número entero no negativo")
        return value

    @field_validator("fecha")
    @classmethod
    def fecha_not_future(cls, value: date) -> date:
        if value > date.today():
            raise ValueError("La fecha no puede estar en el futuro")
        return value


class RecordVenta(BaseModel):
    id: str = Field(min_length=1)
    cliente: str = Field(min_length=1)
    monto: int
    fecha: date
    canal_venta: str

    @field_validator("id")
    @classmethod
    def id_existent(cls, value: str) -> str:
        if not value:
            raise ValueError("El identificador de la venta no puede estar vacío")
        return value

    @field_validator("monto")
    @classmethod
    def monto_must_be_non_negative(cls, value: int) -> int:
        if value < 0:
            raise ValueError("El monto debe ser un número entero no negativo")
        return value

    @field_validator("fecha")
    @classmethod
    def fecha_not_future(cls, value: date) -> date:
        if value > date.today():
            raise ValueError("La fecha no puede estar en el futuro")
        return value


def validar_ventas(records: list[dict]) -> list[RecordVenta]:
    return [RecordVenta(**record) for record in records]

def validar_costos(records: list[dict]) -> list[RecordCosto]:
    return [RecordCosto(**record) for record in records]

from datetime import date, timedelta

import pytest

from src.data.models import ChannelEnum
from src.data.validator import SaleRecord, normalize_channel


def test_normalize_channel_maps_variants() -> None:
    assert normalize_channel("FB Ads") == ChannelEnum.FACEBOOK
    assert normalize_channel("facebook_ads") == ChannelEnum.FACEBOOK
    assert normalize_channel("unknown") == ChannelEnum.OTHER
    assert normalize_channel("google") == ChannelEnum.WEB
    assert normalize_channel("google_ads") == ChannelEnum.WEB
    assert normalize_channel("google adwords") == ChannelEnum.WEB


def test_sale_record_rejects_future_date() -> None:
    with pytest.raises(ValueError):
        SaleRecord(
            fecha=date.today() + timedelta(days=1),
            canal_venta="google",
            costo=12000,
            impresiones=1000,
            clicks=50,
            nuevos_usuarios=8,
        )


def test_sale_record_rejects_negative_values() -> None:
    with pytest.raises(ValueError):
        SaleRecord(
            fecha=date.today(),
            canal_venta="google",
            costo=-12000,
            impresiones=1000,
            clicks=50,
            nuevos_usuarios=8,
        )

    with pytest.raises(ValueError):
        SaleRecord(
            fecha=date.today(),
            canal_venta="google",
            costo=12000,
            impresiones=-1000,
            clicks=50,
            nuevos_usuarios=8,
        )

    with pytest.raises(ValueError):
        SaleRecord(
            fecha=date.today(),
            canal_venta="google",
            costo=12000,
            impresiones=1000,
            clicks=-50,
            nuevos_usuarios=8,
        )

    with pytest.raises(ValueError):
        SaleRecord(
            fecha=date.today(),
            canal_venta="google",
            costo=12000,
            impresiones=1000,
            clicks=50,
            nuevos_usuarios=-8,
        )

from datetime import date, timedelta

import pytest

from src.data.models import ChannelEnum
from src.data.validator import SaleRecord, normalize_channel


def test_normalize_channel_maps_variants() -> None:
    assert normalize_channel("FB Ads") == ChannelEnum.FACEBOOK
    assert normalize_channel("facebook_ads") == ChannelEnum.FACEBOOK
    assert normalize_channel("unknown") == ChannelEnum.OTHER


def test_sale_record_rejects_future_date() -> None:
    with pytest.raises(ValueError):
        SaleRecord(
            transaction_id="t1",
            customer_id="c1",
            amount="10",
            sale_date=date.today() + timedelta(days=1),
            channel="google",
        )

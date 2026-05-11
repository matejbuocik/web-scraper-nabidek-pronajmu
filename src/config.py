from pathlib import Path

import environ
from dotenv import load_dotenv

from disposition import Disposition


load_dotenv(override=False)

_str_to_disposition_map = {
    "1+kk": Disposition.FLAT_1KK,
    "1+1": Disposition.FLAT_1,
    "2+kk": Disposition.FLAT_2KK,
    "2+1": Disposition.FLAT_2,
    "3+kk": Disposition.FLAT_3KK,
    "3+1": Disposition.FLAT_3,
    "4+kk": Disposition.FLAT_4KK,
    "4+1": Disposition.FLAT_4,
    "5++": Disposition.FLAT_5_UP,
    "others": Disposition.FLAT_OTHERS
}

def dispositions_converter(raw_disps: str) -> Disposition:
    flags = Disposition.NONE
    for key in raw_disps.split(","):
        flags |= _str_to_disposition_map[key]
    return flags


def _optional_int(raw: str | None) -> int | None:
    if raw is None:
        return None
    stripped = raw.strip()
    if stripped == "":
        return None
    try:
        return int(stripped)
    except ValueError as e:
        raise ValueError(
            "Price filter env vars (PRICE_MIN_KC, PRICE_MAX_KC) must be a whole "
            f"number in Kč or left unset. Got {raw!r}."
        ) from e


@environ.config(prefix="")
class Config:
    debug: bool = environ.bool_var()
    found_offers_file: Path = environ.var(converter=Path)
    refresh_interval_daytime_minutes: int = environ.var(converter=int)
    refresh_interval_nighttime_minutes: int = environ.var(converter=int)
    dispositions: Disposition = environ.var(converter=dispositions_converter)
    embed_batch_size: int = environ.var(converter=int, default=10)
    price_min_kc: int | None = environ.var(default=None, converter=_optional_int)
    price_max_kc: int | None = environ.var(default=None, converter=_optional_int)

    @environ.config()
    class Discord:
        token = environ.var()
        offers_channel = environ.var(converter=int)
        dev_channel = environ.var(converter=int)

    discord: Discord = environ.group(Discord)


def _validate_price_filter_bounds(c: Config) -> None:
    for env_name, value in (
        ("PRICE_MIN_KC", c.price_min_kc),
        ("PRICE_MAX_KC", c.price_max_kc),
    ):
        if value is not None and value < 0:
            raise ValueError(f"{env_name} must be >= 0 or unset, got {value}.")
    lo, hi = c.price_min_kc, c.price_max_kc
    if lo is not None and hi is not None and lo > hi:
        raise ValueError(
            f"PRICE_MIN_KC ({lo}) must be <= PRICE_MAX_KC ({hi})."
        )


config: Config = Config.from_environ()
_validate_price_filter_bounds(config)

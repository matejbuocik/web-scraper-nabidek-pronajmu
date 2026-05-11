#!/usr/bin/env python3
import asyncio
import logging
from datetime import datetime, timezone
from time import time

import discord
from discord.ext import tasks

from .config import config
from .discord_logger import DiscordLogger
from .offers_storage import OffersStorage
from .scrapers.rental_offer import RentalOffer, offer_matches_price_range
from .scrapers_manager import create_scrapers, fetch_latest_offers


def get_current_daytime() -> bool:
    return 6 <= datetime.now().hour < 22


def refresh_interval_minutes(is_daytime: bool) -> int:
    return (
        config.refresh_interval_daytime_minutes
        if is_daytime
        else config.refresh_interval_nighttime_minutes
    )


def chunk_offers(offers: list[RentalOffer], size: int):
    for i in range(0, len(offers), size):
        yield offers[i : i + size]


def offer_embed(offer: RentalOffer) -> discord.Embed:
    embed = discord.Embed(
        title=offer.title,
        url=offer.link,
        description=offer.location,
        timestamp=datetime.now(timezone.utc),
        color=offer.scraper.color,
    )
    embed.add_field(name="Cena", value=f"{offer.price} Kč")
    embed.set_author(name=offer.scraper.name, icon_url=offer.scraper.logo_url)
    embed.set_image(url=offer.image_url)
    return embed


client = discord.Client(intents=discord.Intents.default())
daytime = get_current_daytime()
interval_time = refresh_interval_minutes(daytime)

scrapers = create_scrapers(config.dispositions)

@client.event
async def on_ready():
    global channel, storage

    dev_channel = client.get_channel(config.discord.dev_channel)
    channel = client.get_channel(config.discord.offers_channel)
    storage = OffersStorage(config.found_offers_file)

    if not config.debug:
        discord_error_logger = DiscordLogger(client, dev_channel, logging.ERROR)
        logging.getLogger().addHandler(discord_error_logger)
    else:
        logging.info("Discord logger is inactive in debug mode")

    logging.info("Available scrapers: " + ", ".join([s.name for s in scrapers]))

    logging.info("Fetching latest offers every {} minutes".format(interval_time))

    process_latest_offers.start()

@tasks.loop(minutes=interval_time)
async def process_latest_offers():
    logging.info("Fetching offers")

    new_offers = [
        o for o in fetch_latest_offers(scrapers) if not storage.contains(o)
    ]

    first_time = storage.first_time
    storage.save_offers(new_offers)

    offers_to_announce = [
        o
        for o in new_offers
        if offer_matches_price_range(o, config.price_min_kc, config.price_max_kc)
    ]
    skipped_price = len(new_offers) - len(offers_to_announce)
    if skipped_price:
        logging.info(
            "Excluded {} new offers outside price range (min={}, max={} Kč)".format(
                skipped_price, config.price_min_kc, config.price_max_kc
            )
        )

    logging.info(
        "Offers fetched (new: {}, to announce: {})".format(
            len(new_offers), len(offers_to_announce)
        )
    )

    if not first_time:
        for offer_batch in chunk_offers(offers_to_announce, config.embed_batch_size):
            embeds = [offer_embed(o) for o in offer_batch]
            await retry_until_successful_send(channel, embeds)
            await asyncio.sleep(1.5)
    else:
        logging.info("No previous offers, first fetch is running silently")

    global daytime, interval_time
    current_daytime = get_current_daytime()
    if current_daytime != daytime:
        daytime = current_daytime
        interval_time = refresh_interval_minutes(daytime)
        logging.info("Fetching latest offers every {} minutes".format(interval_time))
        process_latest_offers.change_interval(minutes=interval_time)

    await retry_until_successful_edit(channel, f"Last update <t:{int(time())}:R>")


async def retry_until_successful_send(channel: discord.TextChannel, embeds: list[discord.Embed], delay: float = 5.0):
    """Retry sending a message with embeds until it succeeds."""
    while True:
        try:
            await channel.send(embeds=embeds)
            logging.info("Embeds successfully sent.")
            return
        except discord.errors.DiscordServerError as e:
            logging.warning(f"Discord server error while sending embeds: {e}. Retrying in {delay:.1f}s.")
        except discord.errors.HTTPException as e:
            logging.warning(f"HTTPException while sending embeds: {e}. Retrying in {delay:.1f}s.")
        except Exception:
            logging.exception(
                "Unexpected error while sending embeds. Retrying in %.1fs.", delay
            )
            raise
        await asyncio.sleep(delay)


async def retry_until_successful_edit(channel: discord.TextChannel, topic: str, delay: float = 5.0):
    """Retry editing a channel topic until it succeeds."""
    while True:
        try:
            await channel.edit(topic=topic)
            logging.info(f"Channel topic successfully updated to: {topic}")
            return
        except discord.errors.DiscordServerError as e:
            logging.warning(f"Discord server error while editing topic: {e}. Retrying in {delay:.1f}s.")
        except discord.errors.HTTPException as e:
            logging.warning(f"HTTPException while editing topic: {e}. Retrying in {delay:.1f}s.")
        except Exception:
            logging.exception(
                "Unexpected error while editing channel topic. Retrying in %.1fs.",
                delay,
            )
            raise
        await asyncio.sleep(delay)

def main() -> None:
    logging.basicConfig(
        level=(logging.DEBUG if config.debug else logging.INFO),
        format='%(asctime)s - [%(levelname)s] %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S')

    logging.debug("Running in debug mode")

    client.run(config.discord.token, log_level=logging.INFO)


if __name__ == "__main__":
    main()

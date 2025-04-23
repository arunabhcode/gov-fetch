from datetime import datetime, UTC
from uagents import Agent, Context
import calendar

from custom_types import TriggerScrape, DisableTrigger

# --- Controller Agent ---
CHECK_INTERVAL_HOURS = 6  # Check every 6 hours
TRIGGER_INTERVAL_HOURS = 2  # Trigger every 2 hours when active


class ControllerAgent(Agent):
    def __init__(
        self,
        name: str,
        seed: str,
        scraper_address: str,
    ):
        super().__init__(name=name, seed=seed)
        self._scraper_address = scraper_address
        self._trigger_enabled = True
        self._last_checked_month = datetime.now(UTC).month
        self._initial_check_done = False
        self.on_message(model=DisableTrigger, replies=None)(self.handle_disable)
        self.on_interval(period=CHECK_INTERVAL_HOURS * 3600.0)(self.periodic_check)

    async def handle_disable(self, ctx: Context, sender: str, msg: DisableTrigger):
        if msg.disable:
            ctx.logger.info(
                f"Received disable signal from {sender}. Disabling triggers until next month."
            )
            self._trigger_enabled = False

    async def periodic_check(self, ctx: Context):
        now = datetime.now(UTC)
        ctx.logger.debug(
            f"Periodic check at {now}. Current state: enabled={self._trigger_enabled}, last_month={self._last_checked_month}, current_month={now.month}"
        )

        # Perform startup check for when it is first launched
        if not self._initial_check_done:
            await self.run_startup_check(ctx)

        # Reset trigger enable flag at the start of a new month
        if now.month != self._last_checked_month:
            ctx.logger.info(f"New month ({now.month}) detected. Enabling triggers.")
            self._trigger_enabled = True
            self._last_checked_month = now.month
            self._initial_check_done = False  # Allow startup check again

        # Check if triggers are enabled and it's the first day of the month
        if self._trigger_enabled:
            # Check if the current hour is one of the trigger hours (0, 2, 4, ...)
            if now.hour % TRIGGER_INTERVAL_HOURS == 0:
                ctx.logger.info(
                    f"Start of month and trigger hour ({now.hour}:00). Sending trigger."
                )
                await self.send_trigger(ctx)
            else:
                ctx.logger.debug(
                    f"Start of month, but not a trigger hour ({now.hour}:00). Waiting."
                )
        elif not self._trigger_enabled:
            ctx.logger.debug("Triggers are currently disabled.")
        else:
            ctx.logger.debug("Not the start of the month. Waiting.")

    async def run_startup_check(self, ctx: Context):
        """Checks if a trigger should be sent immediately on startup/new month."""
        now = datetime.now(UTC)
        ctx.logger.info("Running startup/new month check.")
        if (
            self._trigger_enabled or not self._initial_check_done
        ) and now.hour % TRIGGER_INTERVAL_HOURS == 0:
            ctx.logger.info(
                f"Startup/New month condition met ({now.day=}, {now.hour=}). Sending initial trigger."
            )
            await self.send_trigger(ctx)
            self._initial_check_done = True
        else:
            ctx.logger.info(
                "Startup/New month condition not met. No initial trigger sent."
            )

    def compose_url(self) -> str:
        """Composes the target URL based on the next month and year logic."""
        now = datetime.now(UTC)
        current_year = now.year
        current_month = now.month

        # Calculate target month (next month)
        target_month_num = current_month + 1
        year_offset = 0
        if target_month_num > 12:
            target_month_num = 1
            year_offset = 1  # Year increases if we wrap from Dec to Jan

        # Calculate target year based on *current* month
        # If current month is Oct, Nov, Dec, target year is next year
        # Otherwise, it's current year.
        # Note: The year_offset for Dec->Jan wrap is handled separately
        if current_month >= 10:  # October or later
            target_year = current_year + 1
        else:
            target_year = current_year

        # Ensure Dec->Jan wrap correctly affects year if it wasn't already bumped
        if year_offset == 1 and current_month < 10:
            target_year = current_year + 1

        # Get lowercase month name
        try:
            target_month_name = calendar.month_name[target_month_num].lower()
        except IndexError:
            # Should not happen with valid month calculation
            target_month_name = "invalid_month"

        # Assemble URL
        base_url = (
            "https://travel.state.gov/content/travel/en/legal/visa-law0/visa-bulletin/"
        )
        url = f"{base_url}{target_year}/visa-bulletin-for-{target_month_name}-{current_year}.html"
        return url

    async def send_trigger(self, ctx: Context):
        """Sends the TriggerScrape message to the scraper with the composed URL."""
        target_url = (
            self.compose_url()
        )  # compose url added here because if this is perma deployed, url might change
        ctx.logger.info(f"Composed target URL: {target_url}")
        try:
            await ctx.send(
                self._scraper_address, TriggerScrape(trigger=True, url=target_url)
            )
            ctx.logger.info(f"Sent TriggerScrape to {self._scraper_address}")
        except Exception as e:
            ctx.logger.error(
                f"Failed to send TriggerScrape to {self._scraper_address}: {e}"
            )

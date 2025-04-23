import asyncio
from datetime import datetime, UTC
from uagents import Agent, Context, Model


# --- Models ---
class TriggerScrape(Model):
    trigger: bool


class DisableTrigger(Model):
    disable: bool


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

    async def send_trigger(self, ctx: Context):
        """Sends the TriggerScrape message to the scraper."""
        try:
            await ctx.send(self._scraper_address, TriggerScrape(trigger=True))
            ctx.logger.info(f"Sent TriggerScrape to {self._scraper_address}")
        except Exception as e:
            ctx.logger.error(
                f"Failed to send TriggerScrape to {self._scraper_address}: {e}"
            )

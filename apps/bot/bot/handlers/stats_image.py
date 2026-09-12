"""Matplotlib chart rendering for /stats image mode (lazy-imported)."""

from __future__ import annotations

import io
from typing import Any

from telegram import Update

from bot.handlers.stats_summary import (
    _coerce_status_counts,
    _coerce_submissions_by_day,
    format_stats_caption,
)
from bot.handlers.stats_tokens import BRASS, INK, PAPER, SAGE


def render_stats_chart_png(payload: dict[str, Any]) -> bytes:
    """Build a PNG with status bars and a submission sparkline."""
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    status_counts = _coerce_status_counts(payload)
    submissions_by_day = _coerce_submissions_by_day(payload)

    if not status_counts and not submissions_by_day:
        raise ValueError("No chart data available for stats render.")

    panel_count = int(bool(status_counts)) + int(bool(submissions_by_day))
    figure, axes = plt.subplots(
        panel_count,
        1,
        figsize=(6.5, 2.8 * panel_count),
    )
    axis_list = [axes] if panel_count == 1 else list(axes)

    figure.patch.set_facecolor(PAPER)
    axis_index = 0

    if status_counts:
        axis = axis_list[axis_index]
        axis_index += 1
        ordered = sorted(
            status_counts.items(),
            key=lambda item: (-item[1], item[0]),
        )
        labels = [status.replace("_", " ") for status, _ in ordered]
        values = [count for _, count in ordered]
        colors = [BRASS if label == "escalated" else SAGE for label in labels]
        axis.barh(labels, values, color=colors)
        axis.set_title("Status breakdown", color=INK, fontsize=11, loc="left")
        axis.tick_params(colors=INK, labelsize=9)
        axis.set_facecolor(PAPER)
        for spine in axis.spines.values():
            spine.set_color(INK)

    if submissions_by_day:
        axis = axis_list[axis_index]
        recent = submissions_by_day[-14:]
        dates = [str(item.get("date") or "") for item in recent]
        counts = [int(item.get("count") or 0) for item in recent]
        axis.plot(range(len(counts)), counts, color=BRASS, linewidth=2, marker="o")
        axis.fill_between(range(len(counts)), counts, color=BRASS, alpha=0.15)
        axis.set_title("Submissions (recent days)", color=INK, fontsize=11, loc="left")
        axis.set_xticks(range(len(dates)))
        axis.set_xticklabels([day[5:] for day in dates], rotation=45, ha="right")
        axis.tick_params(colors=INK, labelsize=8)
        axis.set_facecolor(PAPER)
        for spine in axis.spines.values():
            spine.set_color(INK)

    figure.tight_layout()
    buffer = io.BytesIO()
    try:
        figure.savefig(buffer, format="png", dpi=120, facecolor=PAPER)
    finally:
        plt.close(figure)
    return buffer.getvalue()


async def deliver_stats_image(update: Update, payload: dict[str, Any]) -> None:
    """Render dashboard charts and send as a Telegram photo."""
    if update.message is None:
        return

    png_bytes = render_stats_chart_png(payload)
    buffer = io.BytesIO(png_bytes)
    buffer.name = "hospi-stats.png"
    caption = format_stats_caption(payload)
    await update.message.reply_photo(photo=buffer, caption=caption)

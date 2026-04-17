from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go

ZMANIM_PLOT_COLUMNS = [
    "sunrise",
    "alos_nautical_edge",
    "alos_astronomical_edge",
    "misheyakir",
    "latest_shema",
    "latest_shacharit",
    "earliest_mincha",
    "mincha_ketana",
    "plag_hamincha",
    "solar_noon",
    "sunset",
    "candle_lighting",
    "tzais_three_stars",
    "tzais_civil_end",
    "shabbat_ends",
    "chatzot_halaila",
]


class ZmanimPlotter:
    @staticmethod
    def time_to_minutes(series: pd.Series) -> pd.Series:
        dt = pd.to_datetime(series.str.slice(0, 19), errors="coerce")
        return dt.dt.hour * 60 + dt.dt.minute + dt.dt.second / 60.0

    @staticmethod
    def minutes_to_hhmmss_format(m: float) -> str:
        if pd.isna(m):
            return ""

        total = int(round(m * 60))
        hh = (total // 3600) % 24
        mm = (total % 3600) // 60
        ss = total % 60
        return f"{hh:02d}:{mm:02d}:{ss:02d}"

    def plot_zmanim(self, df: pd.DataFrame, title: str = "Zmanim (Local Time)") -> go.Figure:
        x = pd.to_datetime(df["date"], errors="coerce")

        fig = go.Figure()
        for col in ZMANIM_PLOT_COLUMNS:
            y = self.time_to_minutes(df[col])
            hover_times = y.apply(self.minutes_to_hhmmss_format)

            fig.add_trace(
                go.Scatter(
                    x=x,
                    y=y,
                    mode="lines+markers",
                    name=col,
                    customdata=hover_times,
                    hovertemplate="Date: %{x|%Y-%m-%d}<br>Time: %{customdata}<extra>%{fullData.name}</extra>",
                )
            )

        tickvals = list(range(0, 24 * 60, 60))
        ticktext = [self.minutes_to_hhmmss_format(t) for t in tickvals]

        fig.update_layout(
            title=title,
            xaxis_title="Date",
            yaxis={
                "title": "Time of Day",
                "range": [0, 1439],
                "tickmode": "array",
                "tickvals": tickvals,
                "ticktext": ticktext,
                "autorange": False,
            },
            legend_title="Zman",
        )
        return fig

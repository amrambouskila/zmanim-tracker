from __future__ import annotations

from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

import pandas as pd
import streamlit as st

from src.engine.zmanim_calculator import ZmanimCalculatorAngleBased
from src.engine.zmanim_data_builder import ZmanimDataBuilder
from src.location.location_resolver import LocationResolver
from src.models.location import Location
from src.visualization.zmanim_plotter import ZmanimPlotter

TODAYS_ZMANIM_DISPLAY_ORDER = [
    "alos_astronomical_edge",
    "alos_nautical_edge",
    "misheyakir",
    "sunrise",
    "latest_shema",
    "latest_shacharit",
    "solar_noon",
    "earliest_mincha",
    "mincha_ketana",
    "plag_hamincha",
    "sunset",
    "candle_lighting",
    "tzais_three_stars",
    "tzais_civil_end",
    "chatzot_halaila",
    "shabbat_ends",
]


class ZmanimApp:
    def __init__(
        self,
        location_resolver: LocationResolver | None = None,
        zmanim_calculator: ZmanimCalculatorAngleBased | None = None,
        zmanim_plotter: ZmanimPlotter | None = None,
    ) -> None:
        self.location_resolver = location_resolver if location_resolver is not None else LocationResolver()
        self.zmanim_calculator = (
            zmanim_calculator if zmanim_calculator is not None else ZmanimCalculatorAngleBased()
        )
        self.zmanim_data_builder = ZmanimDataBuilder(self.zmanim_calculator)
        self.zmanim_plotter = zmanim_plotter if zmanim_plotter is not None else ZmanimPlotter()

    def render_todays_zmanim(self, df: pd.DataFrame, loc: Location) -> None:
        st.subheader("Today's Zmanim")

        today_local = datetime.now(ZoneInfo(loc.timezone)).date()
        today_str = today_local.isoformat()

        row = df.loc[df["date"] == today_str]
        if row.empty:
            st.info(f"No row for today ({today_str}). Adjust your date range.")
            return

        r = row.iloc[0].to_dict()

        items: list[tuple[str, str]] = []
        for k in TODAYS_ZMANIM_DISPLAY_ORDER:
            if k in r:
                v = str(r[k]).strip()
                if v and v != "nan":
                    items.append((k, v))

        if not items:
            st.info("No zmanim available to display for today.")
            return

        cols = st.columns(3)
        for i, (k, v) in enumerate(items):
            cols[i % 3].metric(label=k, value=v)

    def run(self) -> None:
        st.set_page_config(page_title="Zmanim Chart", layout="wide")
        st.title("Zmanim Chart")

        with st.sidebar:
            st.header("Inputs")
            location_input = st.text_input(
                "Location (ZIP, city/state, or lat,lon)", value="10001"
            )
            col1, col2 = st.columns(2)
            with col1:
                start_date = st.date_input("Start date", value=date.today())
            with col2:
                end_date = st.date_input("End date", value=date.today() + timedelta(days=14))

            run_btn = st.button("Generate")

        if not run_btn:
            st.info("Set inputs and click Generate.")
            return

        loc = self.location_resolver.resolve(location_input)

        st.subheader("Resolved location")
        st.write(
            {
                "label": loc.label,
                "latitude": loc.latitude,
                "longitude": loc.longitude,
                "timezone": loc.timezone,
            }
        )

        df = self.zmanim_data_builder.build(loc, start_date, end_date)

        self.render_todays_zmanim(df, loc)

        st.subheader("Zmanim Data")
        st.dataframe(df, use_container_width=True)

        st.subheader("Zmanim Visualization")
        fig = self.zmanim_plotter.plot_zmanim(df)
        st.plotly_chart(fig, use_container_width=True)

        st.subheader("Download Zmanim")
        csv = df.to_csv(index=False).encode("utf-8")
        st.download_button("Download CSV", csv, file_name="zmanim.csv", mime="text/csv")


def main() -> None:
    ZmanimApp().run()


if __name__ == "__main__":  # pragma: no cover - streamlit script entry
    main()

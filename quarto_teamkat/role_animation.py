import html
import webbrowser
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
import plotly.io as pio
from google.cloud import bigquery
from plotly.colors import qualitative
from plotly.subplots import make_subplots

DEFAULT_TOP = 10
DEFAULT_MONTHS = 48


def load_data():
    client = bigquery.Client(project="datafolk-prod-94c7")
    return client.query(
        "SELECT dato_mnd, Rolle, antall_totalt "
        "FROM `datafolk-prod-94c7.teamkatalogen_01012023_01112026.rolle_stats` "
        "ORDER BY dato_mnd, antall_totalt DESC, Rolle"
    ).to_dataframe()


def prepare_data(data, months=DEFAULT_MONTHS):
    data = data[["dato_mnd", "Rolle", "antall_totalt"]].copy()
    data["dato_mnd"] = pd.to_datetime(data["dato_mnd"], errors="raise")
    data["dato_mnd"] = data["dato_mnd"].dt.to_period("M").dt.to_timestamp()
    data["antall_totalt"] = pd.to_numeric(data["antall_totalt"], errors="raise")
    if data.empty or data.isna().any().any():
        raise ValueError("Data must contain non-null months, roles and counts.")
    if (
        not data["Rolle"]
        .map(lambda role: isinstance(role, str) and bool(role.strip()))
        .all()
    ):
        raise ValueError("Role names must be non-empty strings.")
    counts = data["antall_totalt"]
    if (counts < 0).any() or (counts % 1 != 0).any():
        raise ValueError("Counts must be non-negative integers.")
    if data.duplicated(["dato_mnd", "Rolle"]).any():
        raise ValueError("Expected exactly one row per role and month.")
    first_month = data["dato_mnd"].max() - pd.DateOffset(months=months - 1)
    data = data.loc[data["dato_mnd"] >= first_month]
    return data.sort_values(
        ["dato_mnd", "antall_totalt", "Rolle"], ascending=[True, False, True]
    )


def growth_summary(data):
    first_month = data["dato_mnd"].min()
    last_month = data["dato_mnd"].max()
    first = data.loc[data["dato_mnd"] == first_month].set_index("Rolle")[
        "antall_totalt"
    ]
    last = data.loc[data["dato_mnd"] == last_month].set_index("Rolle")["antall_totalt"]
    summary = pd.concat([first.rename("Start"), last.rename("Latest")], axis=1)
    summary["Change"] = summary["Latest"] - summary["Start"]
    summary["Growth (%)"] = (
        summary["Change"].div(summary["Start"].where(summary["Start"] > 0)) * 100
    )
    return summary.sort_values("Latest", ascending=False)


def make_animation(data, top=DEFAULT_TOP):
    roles = sorted(data["Rolle"].unique())
    palette = qualitative.Safe + qualitative.Plotly
    colours = {role: palette[index % len(palette)] for index, role in enumerate(roles)}
    months = sorted(data["dato_mnd"].unique())
    frames = []
    for month in months:
        leaders = data.loc[data["dato_mnd"] == month].head(top).iloc[::-1]
        label = pd.Timestamp(month).strftime("%Y-%m")
        frames.append(
            go.Frame(
                name=label,
                data=[
                    go.Bar(
                        x=leaders["antall_totalt"].tolist(),
                        y=leaders["Rolle"].tolist(),
                        orientation="h",
                        marker_color=[colours[role] for role in leaders["Rolle"]],
                        text=leaders["antall_totalt"].tolist(),
                        textposition="outside",
                        cliponaxis=False,
                        hovertemplate="%{y}: %{x:,.0f}<extra></extra>",
                    )
                ],
                layout=go.Layout(
                    title_text=f"Top {top} roles | {label}",
                    yaxis={
                        "categoryorder": "array",
                        "categoryarray": leaders["Rolle"].tolist(),
                    },
                ),
            )
        )
    options = {
        "frame": {"duration": 750, "redraw": True},
        "transition": {"duration": 0},
        "mode": "immediate",
    }
    figure = go.Figure(data=frames[0].data, frames=frames, layout=frames[0].layout)
    figure.update_layout(
        template="plotly_white",
        height=max(450, top * 34 + 180),
        margin={"l": 200, "r": 70, "b": 140},
        showlegend=False,
        xaxis={
            "title": "People with role",
            "range": [0, float(data["antall_totalt"].max()) * 1.15 + 1],
        },
        yaxis={"automargin": True},
        updatemenus=[
            {
                "type": "buttons",
                "direction": "left",
                "x": 0,
                "y": -0.15,
                "buttons": [
                    {
                        "label": "Play",
                        "method": "animate",
                        "args": [None, {**options, "fromcurrent": True}],
                    },
                    {
                        "label": "Pause",
                        "method": "animate",
                        "args": [
                            [None],
                            {**options, "frame": {"duration": 0, "redraw": False}},
                        ],
                    },
                ],
            }
        ],
        sliders=[
            {
                "active": 0,
                "y": -0.27,
                "currentvalue": {"prefix": "Month: "},
                "steps": [
                    {
                        "label": frame.name,
                        "method": "animate",
                        "args": [
                            [frame.name],
                            {**options, "frame": {"duration": 0, "redraw": True}},
                        ],
                    }
                    for frame in frames
                ],
            }
        ],
    )
    return figure


def make_growth_chart(summary, top=DEFAULT_TOP):
    comparable = summary.dropna(subset=["Start", "Latest"])
    selected = comparable.loc[
        comparable["Change"].abs().sort_values(ascending=False).head(top).index
    ]
    selected = selected.sort_values("Change")
    figure = make_subplots(
        rows=1,
        cols=2,
        subplot_titles=("Change in people", "Growth from starting count"),
        horizontal_spacing=0.25,
    )
    for column, metric in enumerate(["Change", "Growth (%)"], start=1):
        figure.add_trace(
            go.Bar(
                x=selected[metric].tolist(),
                y=selected.index.tolist(),
                orientation="h",
                marker_color=[
                    "#15803d" if change >= 0 else "#b91c1c"
                    for change in selected["Change"]
                ],
                customdata=selected[["Start", "Latest"]].to_numpy(),
                hovertemplate="%{y}<br>Value: %{x:.1f}<br>Start: %{customdata[0]:,.0f}<br>Latest: %{customdata[1]:,.0f}<extra></extra>",
            ),
            row=1,
            col=column,
        )
        figure.update_yaxes(
            categoryorder="array",
            categoryarray=selected.index.tolist(),
            automargin=True,
            row=1,
            col=column,
        )
    figure.update_xaxes(title_text="Change in people", zeroline=True, row=1, col=1)
    figure.update_xaxes(title_text="Growth (%)", zeroline=True, row=1, col=2)
    figure.update_layout(
        title_text=f"Largest absolute changes | {len(comparable)} roles present at both endpoints",
        template="plotly_white",
        showlegend=False,
        height=max(450, len(selected) * 34 + 160),
        margin={"l": 200, "r": 50},
    )
    return figure


def write_report(data, output, top=DEFAULT_TOP):
    summary = growth_summary(data)
    first_month = data["dato_mnd"].min()
    last_month = data["dato_mnd"].max()
    expected = pd.date_range(first_month, last_month, freq="MS")
    missing = expected.difference(data["dato_mnd"].unique())
    missing_text = ", ".join(missing.strftime("%Y-%m")) or "None"
    excluded = summary[["Start", "Latest"]].isna().any(axis=1).sum()
    animation = pio.to_html(
        make_animation(data, top),
        full_html=False,
        include_plotlyjs=True,
        auto_play=False,
    )
    growth = pio.to_html(
        make_growth_chart(summary, top), full_html=False, include_plotlyjs=False
    )
    table = summary.to_html(
        float_format=lambda value: f"{value:,.1f}", na_rep="Not available", border=0
    )
    document = f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Role history</title><style>
body {{ font-family: sans-serif; max-width: 1400px; margin: 24px auto; padding: 0 16px; color: #242424; }}
.chart, .table {{ overflow-x: auto; }}
th, td {{ padding: 8px 16px; text-align: right; border-bottom: 1px solid #ddd; }}
th:first-child {{ text-align: left; }}
</style></head><body>
<h1>Role history</h1>
<p>{first_month:%Y-%m} to {last_month:%Y-%m}. Counts are per role; a person can hold multiple roles.</p>
<div class="chart">{animation}</div>
<h2>Growth summary</h2>
<p>First versus last observed month. Missing observations are not treated as zero.
{excluded} roles excluded from growth comparisons because an endpoint is missing.
Percentage growth is unavailable when the starting count is zero or missing.</p>
<p>Missing months: {html.escape(missing_text)}.</p>
<div class="chart">{growth}</div>
<div class="table">{table}</div>
</body></html>"""
    output = Path(output).expanduser().resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(document, encoding="utf-8")
    print(summary.round(1).to_string(na_rep="Not available"))
    print(f"\nReport: {output.as_uri()}")
    return output


def main():
    data = prepare_data(load_data())
    output = write_report(data, Path(__file__).with_suffix(".html"))
    webbrowser.open(output.as_uri())


if __name__ == "__main__":
    main()

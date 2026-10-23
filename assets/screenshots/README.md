# Power BI screenshot capture guide

The saved PBIX has one 1280 × 720 report page, **Page 1**. An earlier version contained a visible text box with a name and student number. The current saved report definition has that text box blank. Check the live page before capturing, and inspect the rest of the page for identifying information as well.

Use the open report in Power BI Desktop, not an image generated from the PBIX metadata. Select **View → Page view → Fit to page** for a full-page capture. If the charts are loading, wait until they display their values. Windows **Snipping Tool** (`Win` + `Shift` + `S`) can capture the report canvas; save PNG files to `outputs/screenshots/`. Capture only the report canvas and exclude the Power BI title bar, file paths, account menu, and editing panes. For close-ups, zoom in or snip the indicated region of the actual page. Use sufficient display resolution for readable labels.

| Save as | Capture from Page 1 |
| --- | --- |
| `dashboard-overview.png` | Entire report canvas: four KPI cards, both trend lines, the peak-hours matrix, payment-share donut, tips-by-payment bars, and revenue-by-pickup-borough bars. |
| `dashboard-kpis.png` | Four top-left cards: **Total Trips**, **Total Revenue**, **Avg Fare**, **Avg Duration**, including their actual displayed values. |
| `dashboard-analysis.png` | Lower analysis row: **Peak Hours (Trips)** matrix, **Tips by Payment Label** bars, and **Payment Share** donut. Keep chart titles and labels visible. |
| `dashboard-trends.png` | Middle row: the trips-by-pickup-date and revenue-by-pickup-date line charts, including axes and legends. |
| `dashboard-geography.png` | Right-side **Revenue by Pickup Borough** bar chart, including title and borough labels. This is a borough comparison, not a map. |

All five current PNGs are views of the **same** report page and are embedded in the project README. The capture named `dashboard-analysis.png` shows only the peak-hours matrix and its first visible hours; it could be replaced with a wider capture showing the three lower-row visuals. Matching copies in `outputs/screenshots/` preserve the provided captures, while the files here supply the README images.

const DATA_PATH = "data/nba_team_game_1999_2023.csv";

const TEAM_NAMES = {
  ATL: "Atlanta Hawks",
  BOS: "Boston Celtics",
  BKN: "Brooklyn Nets",
  CHA: "Charlotte Hornets",
  CHI: "Chicago Bulls",
  CLE: "Cleveland Cavaliers",
  DAL: "Dallas Mavericks",
  DEN: "Denver Nuggets",
  DET: "Detroit Pistons",
  GSW: "Golden State Warriors",
  HOU: "Houston Rockets",
  IND: "Indiana Pacers",
  LAC: "Los Angeles Clippers",
  LAL: "Los Angeles Lakers",
  MEM: "Memphis Grizzlies",
  MIA: "Miami Heat",
  MIL: "Milwaukee Bucks",
  MIN: "Minnesota Timberwolves",
  NOP: "New Orleans Pelicans",
  NYK: "New York Knicks",
  OKC: "Oklahoma City Thunder",
  ORL: "Orlando Magic",
  PHI: "Philadelphia 76ers",
  PHX: "Phoenix Suns",
  POR: "Portland Trail Blazers",
  SAC: "Sacramento Kings",
  SAS: "San Antonio Spurs",
  TOR: "Toronto Raptors",
  UTA: "Utah Jazz",
  WAS: "Washington Wizards",
};

const state = {
  rawData: [],
  seasons: [],
  teams: [],
  gameTypes: [],
  filters: {
    seasonLabel: "All",
    team: "All",
    seasonType: "All",
  },
  timeRange: {
    min: null,
    max: null,
  },
  lineListenerAttached: false,
};

const colorMap = {
  Win: "#1f77b4",
  Loss: "#d62728",
};

function getTeamName(abbr) {
  const key = String(abbr || "").trim().toUpperCase();
  return TEAM_NAMES[key] || abbr;
}

// 3-type mapping:
// Regular Season -> circle
// Playoffs -> triangle-up
// Pre Season -> square
function seasonSymbol(seasonType) {
  const normalized = String(seasonType).toLowerCase();
  if (normalized.includes("pre")) return "square";
  if (normalized.includes("playoff")) return "triangle-up";
  return "circle";
}

function loadData() {
  Papa.parse(DATA_PATH, {
    download: true,
    header: true,
    skipEmptyLines: true,
    complete: (results) => {
      const parsed = results.data
        .map((row) => ({
          ...row,
          dateObj: new Date(row.date),
          points: Number.parseFloat(row.points),
          fg_pct: Number.parseFloat(row.fg_pct),
          season_year: Number.parseInt(row.season_year, 10),
        }))
        .filter(
          (row) =>
            !Number.isNaN(row.dateObj.getTime()) &&
            Number.isFinite(row.points) &&
            Number.isFinite(row.fg_pct) &&
            Number.isFinite(row.season_year)
        );

      state.rawData = parsed;
      state.seasons = [...new Set(parsed.map((d) => d.season_year))].sort((a, b) => a - b);
      state.teams = [...new Set(parsed.map((d) => d.team))].sort();
      state.gameTypes = [...new Set(parsed.map((d) => d.season_type))].sort();

      state.timeRange.min = Math.min(...state.seasons);
      state.timeRange.max = Math.max(...state.seasons);

      console.log(
        `Loaded rows: ${parsed.length}, Unique seasons: ${state.seasons.length}, Unique teams: ${state.teams.length}`
      );
      console.log("Game types:", state.gameTypes);

      initControls();
      updateAllViews();
    },
    error: (err) => {
      console.error("Failed to load CSV:", err);
    },
  });
}

function initControls() {
  const seasonSelect = document.getElementById("season-filter");
  const teamSelect = document.getElementById("team-filter");
  const typeSelect = document.getElementById("type-filter");

  const seasonLabels = [...new Map(state.rawData.map((d) => [d.season_year, d.season_label])).entries()]
    .sort((a, b) => a[0] - b[0])
    .map((entry) => entry[1]);

  buildOptions(seasonSelect, ["All", ...seasonLabels]);
  buildOptions(teamSelect, ["All", ...state.teams]);
  buildOptions(typeSelect, ["All", ...state.gameTypes]);

  seasonSelect.addEventListener("change", (e) => {
    state.filters.seasonLabel = e.target.value;
    syncTimeRangeToFilteredDomain();
    updateAllViews();
  });

  teamSelect.addEventListener("change", (e) => {
    state.filters.team = e.target.value;
    syncTimeRangeToFilteredDomain();
    updateAllViews();
  });

  typeSelect.addEventListener("change", (e) => {
    state.filters.seasonType = e.target.value;
    syncTimeRangeToFilteredDomain();
    updateAllViews();
  });
}

function buildOptions(selectEl, values) {
  if (selectEl.id === "team-filter") {
    selectEl.innerHTML = values
      .map((v) => `<option value="${v}">${v === "All" ? "All" : getTeamName(v)}</option>`)
      .join("");
    return;
  }

  selectEl.innerHTML = values.map((v) => `<option value="${v}">${v === "All" ? "All" : v}</option>`).join("");
}

function getFilteredData({ applyTime = true } = {}) {
  let filtered = state.rawData;

  if (state.filters.seasonLabel !== "All") {
    filtered = filtered.filter((d) => d.season_label === state.filters.seasonLabel);
  }
  if (state.filters.team !== "All") {
    filtered = filtered.filter((d) => d.team === state.filters.team);
  }
  if (state.filters.seasonType !== "All") {
    filtered = filtered.filter((d) => d.season_type === state.filters.seasonType);
  }

  if (applyTime) {
    filtered = filtered.filter(
      (d) => d.season_year >= state.timeRange.min && d.season_year <= state.timeRange.max
    );
  }

  return filtered;
}

function syncTimeRangeToFilteredDomain() {
  const noTimeData = getFilteredData({ applyTime: false });
  if (!noTimeData.length) {
    state.timeRange.min = Math.min(...state.seasons);
    state.timeRange.max = Math.max(...state.seasons);
    return;
  }

  const minYear = Math.min(...noTimeData.map((d) => d.season_year));
  const maxYear = Math.max(...noTimeData.map((d) => d.season_year));

  state.timeRange.min = Math.max(state.timeRange.min, minYear);
  state.timeRange.max = Math.min(state.timeRange.max, maxYear);

  if (state.timeRange.min > state.timeRange.max) {
    state.timeRange.min = minYear;
    state.timeRange.max = maxYear;
  }
}

function updateAllViews() {
  const filtered = getFilteredData({ applyTime: true });
  const noTimeFiltered = getFilteredData({ applyTime: false });

  renderScatter(filtered);
  renderBar(filtered);
  renderLine(noTimeFiltered);
}

// Dynamic grouping by (season_type, win) so Pre Season does not get merged into Regular
function renderScatter(data) {
  const seasonTypes = [...new Set(data.map((d) => d.season_type))].sort();
  const winStates = ["Win", "Loss"];
  const traces = [];

  for (const seasonType of seasonTypes) {
    for (const winKey of winStates) {
      const rows = data.filter((d) => d.season_type === seasonType && d.win === winKey);
      if (!rows.length) continue;

      traces.push({
        type: "scattergl",
        mode: "markers",
        name: `${seasonType} - ${winKey}`,
        x: rows.map((d) => d.fg_pct),
        y: rows.map((d) => d.points),
        customdata: rows.map((d) => [
          getTeamName(d.team),
          getTeamName(d.opponent),
          d.points,
          d.fg_pct,
          d.season_label,
          d.season_type,
        ]),
        hovertemplate:
          "Team: %{customdata[0]}<br>" +
          "Opponent: %{customdata[1]}<br>" +
          "Points: %{customdata[2]:.0f}<br>" +
          "FG%: %{customdata[3]:.1%}<br>" +
          "Season: %{customdata[4]}<br>" +
          "Game Type: %{customdata[5]}<extra></extra>",
        marker: {
          color: colorMap[winKey],
          symbol: seasonSymbol(seasonType),
          size: 8,
          opacity: 0.78,
          line: { width: 0.4, color: "#ffffff" },
        },
        showlegend: true,
      });
    }
  }

  const layout = {
    margin: { t: 20, r: 18, b: 50, l: 56 },
    paper_bgcolor: "#ffffff",
    plot_bgcolor: "#ffffff",
    xaxis: {
      title: "Field Goal %",
      tickformat: ".0%",
      gridcolor: "#edf0f3",
      zeroline: false,
    },
    yaxis: {
      title: "Total Points",
      gridcolor: "#edf0f3",
      zeroline: false,
    },
    hoverlabel: { bgcolor: "#111827" },
    legend: { orientation: "h", y: 1.12, x: 0, font: { size: 11 } },
  };

  Plotly.react("scatter-chart", traces, layout, {
    responsive: true,
    displayModeBar: false,
  });
}

function renderBar(data) {
  const groups = { Home: [], Away: [] };
  data.forEach((d) => {
    if (d.home_away === "Home") groups.Home.push(d.points);
    if (d.home_away === "Away") groups.Away.push(d.points);
  });

  const avg = (arr) => (arr.length ? arr.reduce((a, b) => a + b, 0) / arr.length : 0);
  const yValues = [avg(groups.Home), avg(groups.Away)];

  const trace = {
    type: "bar",
    x: ["Home", "Away"],
    y: yValues,
    marker: {
      color: ["#4c78a8", "#f58518"],
      line: { width: 0 },
    },
    text: yValues.map((v) => v.toFixed(1)),
    textposition: "outside",
    hovertemplate: "%{x}: %{y:.2f}<extra></extra>",
  };

  const layout = {
    margin: { t: 14, r: 12, b: 40, l: 50 },
    paper_bgcolor: "#ffffff",
    plot_bgcolor: "#ffffff",
    yaxis: {
      title: "Avg Points",
      gridcolor: "#edf0f3",
      zeroline: false,
    },
    xaxis: { title: "" },
  };

  Plotly.react("bar-chart", [trace], layout, {
    responsive: true,
    displayModeBar: false,
  });
}

function renderLine(dataWithoutTimeFilter) {
  const grouped = new Map();

  dataWithoutTimeFilter.forEach((d) => {
    if (!grouped.has(d.season_year)) grouped.set(d.season_year, []);
    grouped.get(d.season_year).push(d.points);
  });

  const seasonsSorted = [...grouped.keys()].sort((a, b) => a - b);
  const avgPoints = seasonsSorted.map((year) => {
    const values = grouped.get(year);
    return values.reduce((sum, val) => sum + val, 0) / values.length;
  });

  const trace = {
    type: "scatter",
    mode: "lines+markers",
    x: seasonsSorted,
    y: avgPoints,
    line: { color: "#0f766e", width: 2.5 },
    marker: { color: "#0f766e", size: 6 },
    hovertemplate: "Season %{x}: %{y:.2f} pts<extra></extra>",
    showlegend: false,
  };

  // When only one season is selected, avoid a zero-width x-axis range.
  const xMin = state.timeRange.min;
  const xMax = state.timeRange.max;
  const xRange = xMin === xMax ? [xMin - 0.5, xMax + 0.5] : [xMin, xMax];

  const layout = {
    margin: { t: 14, r: 12, b: 48, l: 50 },
    paper_bgcolor: "#ffffff",
    plot_bgcolor: "#ffffff",
    xaxis: {
      title: "Season Year",
      tickmode: "linear",
      dtick: 2,
      range: xRange,
      rangeslider: {
        visible: true,
        bgcolor: "#eef2f7",
        bordercolor: "#d0d5dd",
      },
      gridcolor: "#edf0f3",
    },
    yaxis: {
      title: "Avg Points",
      gridcolor: "#edf0f3",
      zeroline: false,
    },
  };

  Plotly.react("line-chart", [trace], layout, {
    responsive: true,
    displayModeBar: false,
  });

  if (!state.lineListenerAttached) {
    const lineNode = document.getElementById("line-chart");
    lineNode.on("plotly_relayout", (eventData) => {
      const left = eventData["xaxis.range[0]"];
      const right = eventData["xaxis.range[1]"];
      const auto = eventData["xaxis.autorange"];

      if (auto) {
        state.timeRange.min = Math.min(...state.seasons);
        state.timeRange.max = Math.max(...state.seasons);
        const filtered = getFilteredData({ applyTime: true });
        renderScatter(filtered);
        renderBar(filtered);
        return;
      }

      if (left !== undefined && right !== undefined) {
        state.timeRange.min = Math.round(Number(left));
        state.timeRange.max = Math.round(Number(right));

        if (state.timeRange.min > state.timeRange.max) {
          const tmp = state.timeRange.min;
          state.timeRange.min = state.timeRange.max;
          state.timeRange.max = tmp;
        }

        const filtered = getFilteredData({ applyTime: true });
        renderScatter(filtered);
        renderBar(filtered);
      }
    });

    state.lineListenerAttached = true;
  }
}

loadData();

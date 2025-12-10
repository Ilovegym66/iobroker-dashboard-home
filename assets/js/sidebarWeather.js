/**
 * sidebarWeatherJS – Wetter aus ioBroker-States (Wetterstation)
 *
 * Konfiguration (data/sidebar.json → openWeatherMap):
 *
 * "openWeatherMap": {
 *   "enabled": true,
 *   "imageSet": 1,
 *   "imageType": "svg",
 *   "temperatureId": "0_userdata.0.Weather.Ecowitt.outside.temperature_C",
 *   "conditionId":  "0_userdata.0.Weather.Brightsky.current.condition",
 *   "humidityId":   "0_userdata.0.Klima.Aussenfeuchte",
 *   "tempMinId":    "0_userdata.0.Weather.Brightsky.current.temp_min_today",
 *   "tempMaxId":    "0_userdata.0.Weather.Brightsky.current.temp_max_today",
 *   "windSpeedId":  "0_userdata.0.Weather.Ecowitt.wind.speed_kmh",
 *   "iconId":       "",                              // optional, kann leer bleiben
 *   "warningsHtmlId": "0_userdata.0.vis.Dashboards.DWD_NINA_PfungstadtHTML"                             // optional: DWD-HTML
 * }
 */

const sidebarWeatherJS = {

  createWeatherDisplay(parentElement, weatherConfig) {
    const cfg = weatherConfig || {};

    // State-IDs
    const temperatureId = cfg.temperatureId || "0_userdata.0.Weather.Ecowitt.outside.temperature_C";
    const conditionId   = cfg.conditionId   || "0_userdata.0.Weather.Brightsky.hourly-00.condition";
    const humidityId    = cfg.humidityId    || "0_userdata.0.Klima.Aussenfeuchte";
    const tempMinId     = cfg.tempMinId     || "0_userdata.0.Weather.Brightsky.current.temp_min_today";
    const tempMaxId     = cfg.tempMaxId     || "0_userdata.0.Weather.Brightsky.current.temp_max_today";
    const windSpeedId   = cfg.windSpeedId   || "0_userdata.0.Weather.Ecowitt.wind.speed_kmh";
    const iconId        = cfg.iconId        || "";
    const warningsHtmlId = cfg.warningsHtmlId || "";

    const imageSet      = cfg.imageSet      || 1;
    const imageType     = cfg.imageType     || "svg";

    // Hauptcontainer
    const container = document.createElement("div");
    container.classList.add("weather-container");

    // Icon
    const weatherIcon = document.createElement("img");
    weatherIcon.classList.add("weather-icon");

    // Info-Block
    const weatherInfo = document.createElement("div");
    weatherInfo.classList.add("weather-info");

    const weatherTemp = document.createElement("div");
    weatherTemp.classList.add("weather-temp");

    const weatherDesc = document.createElement("div");
    weatherDesc.classList.add("weather-desc");

    const weatherHighLow = document.createElement("div");
    weatherHighLow.classList.add("weather-high-low");

    const weatherWind = document.createElement("div");
    weatherWind.classList.add("weather-wind");

    const weatherHumidity = document.createElement("div");
    weatherHumidity.classList.add("weather-humidity");

    const weatherError = document.createElement("div");
    weatherError.classList.add("weather-error");
    weatherError.style.display = "none";

    const weatherWarnings = document.createElement("div");
    weatherWarnings.classList.add("weather-warnings");

    weatherInfo.appendChild(weatherTemp);
    weatherInfo.appendChild(weatherDesc);
    weatherInfo.appendChild(weatherHighLow);
    weatherInfo.appendChild(weatherWind);
    weatherInfo.appendChild(weatherHumidity);
    weatherInfo.appendChild(weatherError);
    weatherInfo.appendChild(weatherWarnings);

    container.appendChild(weatherIcon);
    container.appendChild(weatherInfo);

    // IDs & Config merken
    container.dataset.temperatureId  = temperatureId;
    container.dataset.conditionId    = conditionId;
    container.dataset.humidityId     = humidityId;
    container.dataset.tempMinId      = tempMinId;
    container.dataset.tempMaxId      = tempMaxId;
    container.dataset.windSpeedId    = windSpeedId;
    container.dataset.iconId         = iconId;
    container.dataset.warningsHtmlId = warningsHtmlId;
    container.dataset.imageSet       = String(imageSet);
    container.dataset.imageType      = imageType;

    parentElement.appendChild(container);

    // Initiales Update
    this._updateFromStates(container, {
      weatherIcon,
      weatherTemp,
      weatherDesc,
      weatherHighLow,
      weatherWind,
      weatherHumidity,
      weatherError,
      weatherWarnings
    });

    // Regelmäßiges Update alle 60 Sekunden
    setInterval(() => {
      this._updateFromStates(container, {
        weatherIcon,
        weatherTemp,
        weatherDesc,
        weatherHighLow,
        weatherWind,
        weatherHumidity,
        weatherError,
        weatherWarnings
      });
    }, 60000);
  },

  _updateFromStates(container, domRefs) {
    if (typeof ioBrokerStates === "undefined") return;

    const {
      weatherIcon,
      weatherTemp,
      weatherDesc,
      weatherHighLow,
      weatherWind,
      weatherHumidity,
      weatherError,
      weatherWarnings
    } = domRefs;

    const getVal = (id) => {
      if (!id) return null;
      const state = ioBrokerStates[id];
      if (!state || state.val === undefined || state.val === null) return null;
      return state.val;
    };

    const temp      = getVal(container.dataset.temperatureId);
    const cond      = getVal(container.dataset.conditionId);
    const humidity  = getVal(container.dataset.humidityId);
    const tMin      = getVal(container.dataset.tempMinId);
    const tMax      = getVal(container.dataset.tempMaxId);
    const wind      = getVal(container.dataset.windSpeedId);
    const iconVal   = getVal(container.dataset.iconId);
    const warnings  = getVal(container.dataset.warningsHtmlId);

    // Fehleranzeige aus
    weatherError.style.display = "none";
    weatherError.textContent = "";

    // Temperatur
    if (temp !== null) {
      const t = Number(temp);
      weatherTemp.textContent = t.toFixed(1) + "°C";
    } else {
      weatherTemp.textContent = "";
    }

    // Beschreibung
    if (cond !== null && cond !== "") {
      weatherDesc.textContent = String(cond);
    } else {
      weatherDesc.textContent = "";
    }

    // Min/Max
    const parts = [];
    if (tMax !== null) parts.push("H: " + Number(tMax).toFixed(1) + "°C");
    if (tMin !== null) parts.push("T: " + Number(tMin).toFixed(1) + "°C");
    weatherHighLow.textContent = parts.join("   ");

    // Wind
    if (wind !== null) {
      const w = Number(wind);
      weatherWind.textContent = "Wind: " + w.toFixed(1) + " m/s";
    } else {
      weatherWind.textContent = "";
    }

    // Luftfeuchtigkeit
    if (humidity !== null) {
      const h = Number(humidity);
      weatherHumidity.textContent = "Luftfeuchtigkeit: " + h.toFixed(0) + " %";
    } else {
      weatherHumidity.textContent = "";
    }

    // Wetterwarnungen (optional, HTML)
    if (warnings && typeof warnings === "string") {
      weatherWarnings.innerHTML = warnings;
    } else if (warnings) {
      weatherWarnings.textContent = String(warnings);
    } else {
      weatherWarnings.innerHTML = "";
    }

    // Icon – entweder expliziter OWM-Code oder Mapping per Text
    const imageSet  = container.dataset.imageSet || "1";
    const imageType = container.dataset.imageType || "svg";

    let iconCode = null;

    if (iconVal) {
      const s = String(iconVal).trim();
      // Nur verwenden, wenn es wie ein OWM-Code aussieht (z.B. "01d", "03d")
      if (/^[0-9]{2}[dn]?$/.test(s)) {
        iconCode = s;
      }
    }

    if (!iconCode) {
      iconCode = this._mapConditionToIcon(cond);
    }

    if (iconCode) {
      weatherIcon.src = "assets/img/sidebar/weather/" + imageSet + "/" + iconCode + "." + imageType;
      weatherIcon.style.display = "block";
    } else {
      weatherIcon.style.display = "none";
    }

    if (temp === null && cond === null) {
      weatherError.textContent = "Keine Wetterdaten verfügbar.";
      weatherError.style.display = "block";
    }
  },

  /**
   * Mapping von Textbedingungen (z.B. "dry", "cloudy") auf OWM-Iconcodes
   */
  _mapConditionToIcon(condition) {
    if (!condition) return "01d";

    const c = String(condition).toLowerCase();

    if (c.includes("schnee") || c.includes("snow")) return "13d";
    if (c.includes("gewitter") || c.includes("thunder")) return "11d";
    if (c.includes("regen") || c.includes("shower") || c.includes("rain")) return "09d";
    if (c.includes("nebel") || c.includes("fog")) return "50d";
    if (c.includes("wolken") || c.includes("cloud")) return "03d";

    // "dry" → eher sonnig / trocken
    if (c.includes("dry")) return "01d";

    // Default: sonnig
    return "01d";
  }
};

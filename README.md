# Geoseis

A Python package for event discovery and characterization in geothermal/seismic data.

## Configure data paths

Copy `.env.example` to `.env` in the repository root, then set the paths for your machine. `.env` is ignored by Git, so local paths stay out of commits. `GeoSeisSettings` also reads matching `GEOSEIS_` environment variables, which take precedence over values in `.env`.

```sh
cp .env.example .env
```

Set `GEOSEIS_PROJECT_ROOT`, `GEOSEIS_RAW_DATA_DIR`, and `GEOSEIS_RAW_DIR` in `.env` to the appropriate paths on your machine. Paths are parsed as `pathlib.Path` values and can be accessed from the settings object, for example `settings.RAW_DATA_DIR`.

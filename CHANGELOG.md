# Changelog

## [v1.1.1] – 2026-06-12

### Fixed
- Config Flow: `super().__init__()` fehlte, wodurch neue Einträge stumm fehlschlugen und keine Sensoren erstellt wurden

## [v1.1.0] – 2026-06-09

### Fixed
- Tages- und Monatskosten-Sensor: echter Mitternachts-Reset statt Delta-Akkumulation seit HA-Start
- `period_start_kwh` wird über HA-Neustarts hinweg wiederhergestellt (RestoreEntity)
- Config Flow: `_data` war fälschlicherweise eine Klassenvariable (geteilt zwischen Instanzen)

### Changed
- `state_class` der Periodensensoren von `TOTAL_INCREASING` auf `TOTAL` (erlaubt periodische Resets)

## [v1.0.0] – 2026-06-04

### Added
- Initiales Release
- 18 Gerätetypen (Washer, Dryer, Dishwasher, Fridge, Freezer, TV, Server, PC, Router, Heatpump, AC, Oven, Microwave, Boiler, EV Charger, Light, Pump, Custom)
- Kosten-Sensor (kWh × Strompreis)
- Tageskosten-Sensor mit automatischer Reset-Erkennung
- Monatskosten-Sensor
- Betriebsstatus-Sensor (`läuft` / `aus`) mit einstellbarem Watt-Schwellwert
- 3-Schritt Config Flow über die HA-UI
- Options Flow zum Bearbeiten bestehender Geräte
- Übersetzungen: Deutsch & Englisch
- HACS-kompatibel

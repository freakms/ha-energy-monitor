# Energy Monitor — Home Assistant Custom Integration

> by freakms - ich schwöre feierlich ich bin ein tunichtgut

Erstellt automatisch Kosten-, Tages-, Monats- und Betriebsstatus-Sensoren für beliebige Verbraucher — kein YAML tippen, alles über die HA-UI.

---

## Features

- **18 Gerätetypen** voreingestellt (Trockner, Server, Klimaanlage, Wallbox, ...)
- **Kosten-Sensor** (Gesamtkosten: kWh × Strompreis)
- **Tageskosten-Sensor** (automatische Tagesreset-Erkennung)
- **Monatskosten-Sensor**
- **Betriebsstatus-Sensor** (`läuft` / `aus`) mit einstellbarem Watt-Schwellwert
- Jedes Gerät einzeln konfigurierbar, editierbar und löschbar
- Deutsch & Englisch übersetzt

---

## Installation

### Via HACS (empfohlen)
1. HACS → Integrationen → ⋮ → Benutzerdefinierte Repositories
2. URL: `https://github.com/freakms/ha-energy-monitor` — Typ: Integration
3. Installieren → HA neu starten

### Manuell
1. Ordner `custom_components/energy_monitor/` in dein HA-Konfig-Verzeichnis kopieren
2. HA neu starten

---

## Einrichtung

1. **Einstellungen → Geräte & Dienste → Integration hinzufügen → "Energy Monitor"**
2. Gerätetyp wählen (z.B. Wäschetrockner)
3. Namen vergeben (z.B. `Wäschetrockner`)
4. kWh-Sensor zuordnen (Entity-Suche mit Dropdown!)
5. Optional: Watt-Sensor für Echtzeitanzeige
6. Strompreis-Helfer wählen (z.B. `input_number.strompreis`)
7. Optionen: Tages/Monats-Sensoren, Betriebsstatus

→ Sofort werden folgende Sensoren erstellt:
- `sensor.waeschetrockner_energiekosten` — Gesamtkosten in €
- `sensor.waeschetrockner_kosten_heute` — Tageskosten
- `sensor.waeschetrockner_kosten_monat` — Monatskosten
- `sensor.waeschetrockner_betriebsstatus` — `läuft` / `aus`

---

## Kachel-Beispiel (Lovelace)

```yaml
type: entities
title: Wäschetrockner
entities:
  - entity: sensor.waeschetrockner_energiekosten
    name: Gesamtkosten
  - entity: sensor.waeschetrockner_kosten_heute
    name: Heute
  - entity: sensor.waeschetrockner_kosten_monat
    name: Dieser Monat
  - entity: sensor.waeschetrockner_betriebsstatus
    name: Status
```

---

## Anforderungen

- Home Assistant 2023.6+
- Ein kWh-Sensor (Integralsensor, Verbrauchszähler oder direkte Energiemessung)
- Ein `input_number`-Helfer für den Strompreis (z.B. `input_number.strompreis`)

---

## Lizenz

MIT

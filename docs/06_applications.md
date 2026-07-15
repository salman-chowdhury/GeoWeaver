# Applications

GeoWeaver separates reusable spatial understanding from application-specific objectives.

## CastNetGPT

Initial application and field-test harness.

Primary questions:

- Which eligible shoreline best matches the user's travel, skill, privacy, and family constraints?
- What arrival window best aligns tide, wind, and daylight?
- What should the user inspect before unloading?
- Which factors make the recommendation uncertain?

## Potential future applications

### Flood intelligence

Combine terrain, waterways, rainfall, historic flood extents, and infrastructure to support risk exploration. Any public-facing implementation would require careful validation and explicit limits.

### Property intelligence

Analyse access, amenity, terrain, environmental constraints, transport, and long-term spatial change without pretending to replace professional property, engineering, or planning advice.

### Kayak and shoreline access

Rank launch sites using wind, tide, current, bank slope, parking, facilities, and user ability.

### Wildlife and bird observation

Recommend accessible observation locations based on habitat, season, weather, daylight, and recorded sightings while protecting sensitive species.

### Bushwalking and outdoor photography

Match trails and viewpoints to temperature, rain, cloud, sun angle, accessibility, and crowd preferences.

### Planetary and celestial mapping

The reusable geometry, provenance, feature, and recommendation abstractions may later be extended beyond Earth. Earth-specific assumptions should therefore remain in adapters and objective profiles rather than the core domain model.

## Application contract

Each application should define:

- objective and target outcome;
- hard constraints;
- feature requirements;
- scoring weights or ranking model;
- explanation vocabulary;
- uncertainty policy;
- safety and ethical safeguards;
- evaluation method.

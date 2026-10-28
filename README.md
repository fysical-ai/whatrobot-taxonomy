# whatrobot taxonomy

A MECE hardware taxonomy of robots and robot components, with typed attributes, for [whatro.bot](https://whatro.bot). Modelled on [Shopify's product taxonomy](https://github.com/Shopify/product-taxonomy): source-of-truth YAML in `data/`, generated distributions in `dist/`, an interactive explorer in `docs/`.

**Current version:** see [`VERSION`](VERSION) · **Changelog:** [`CHANGELOG.md`](CHANGELOG.md) · **Explorer:** https://fysical-ai.github.io/whatrobot-taxonomy/ · **Design notes:** [`docs/design.md`](docs/design.md)

## The idea

Every robot and every component sits in **exactly one leaf** of **one hierarchy**, assigned from hardware facts alone — never from who buys it or what it is used for. Everything else (segment, application, autonomy, specs, compatibility, price) is a **typed attribute**: a filter, a comparison column or a cross-link, never a tree branch.

| | Robots (`rb`) | Components (`cp`) |
|---|---|---|
| Classified by | body plan | component type |
| Top level | arm · humanoid · legged · ground · mobile-manipulator · aerial · aquatic · wearable · stationary · kit | end-effector · actuator · sensor · compute · power · structure · teleoperation |
| Max depth | 3 | 3 |

Hybrids are resolved by an ordered list of tie-break rules (kit → wearable → humanoid → legged → aquatic/aerial → mobile manipulator → ground → arm → stationary), implemented in [`whatrobot_taxonomy/classify.py`](whatrobot_taxonomy/classify.py) and regression-tested by [`data/examples.yml`](data/examples.yml). A Spot with an arm is a quadruped; a UR5e on a mobile base sold separately is two entries linked by `compatible_with`.

The design rationale, the four tests for a hierarchy node, and the decision log are in [`docs/design.md`](docs/design.md).

## Who this is for

1. **Integrators** — load `dist/<locale>/{categories,attributes,values}.json` (or `.txt`) into a site, a database or an LLM. Release assets are published gzipped on GitHub Releases as `<basename>.<locale>.<format>.gz` (e.g. `categories.en.json.gz`) and `integrations.<name>.json.gz`.
2. **Taxonomists** — propose changes with an [issue template](.github/ISSUE_TEMPLATE) or a PR against `data/`. See [`CONTRIBUTING.md`](CONTRIBUTING.md).
3. **Developers** — the Python tooling in `whatrobot_taxonomy/` validates `data/` and generates `dist/` and `docs/`.

## Layout

```
data/                       source of truth — CC BY 4.0
  categories/rb_robot.yml     robot tree
  categories/cp_component.yml component tree
  attributes.yml              typed attributes (enum | number | bool | text | ref)
  values.yml                  enum values (friendly_id = <attribute>__<value>)
  application_groups.yml      application → application_group (derived)
  examples.yml                classification regression suite
  integrations/               mappings to ifr-industrial, ifr-service, iso-8373, google, shopify
  localizations/zh-Hans/      Simplified Chinese (LLM draft, pending native review)
dist/                       generated per locale: json + txt; integrations/all_mappings.json
docs/                       static explorer for GitHub Pages, design notes, copy of dist/
schema/                     JSON Schemas generated from the pydantic models
whatrobot_taxonomy/         Python package: models, loader, validate, classify, dist, docs, cli   — MIT
scripts/                    one-off maintenance helpers
tests/                      pytest
```

## Identifiers

Every category, attribute and value has three identifiers:

| | `id` (permanent) | `friendly_id` (data key) | `handle` (URL slug) |
|---|---|---|---|
| Category | `rb-3-1` | `robot.legged.quadruped` | `quadruped` |
| Attribute | `38` | `drive_config` | `drive-config` |
| Value | `90` | `drive_config__differential` | `drive-config__differential` |

Category ids are positional (`<root>-<n>-<n>`) and never renumbered; retired nodes leave gaps. A migration mapping for retired ids (`data/integrations/whatrobot/`) is planned. In `dist/` ids are exposed as `gid://whatrobot/TaxonomyCategory/rb-3-1`.

## Attributes

An attribute is bound to a category node and inherited by every descendant. The two roots carry the universal attributes (manufacturer, segment, application, autonomy, price, …); branch nodes carry the specific ones (`axes` and `reach` on arms, `wheel_feet` on legged robots, `grip_force` on grippers, `reducer_type` on joint modules). `dist/` lists the full effective set on every category.

Unlike Shopify, attributes are typed: `enum` (with `multi`), `number` (with `unit`), `bool`, `text`, `ref`. Every enum ends with `<attr>__other`. `application` is two-level: each value belongs to one `application_group`, derived from `data/application_groups.yml`. "Industrial robots" is not a category or a segment — it is the saved filter `segment: professional` + `application_group: manufacturing`.

## Quick start

```bash
git clone https://github.com/fysical-ai/whatrobot-taxonomy && cd whatrobot-taxonomy
pip install -e ".[dev]"                                   # editable install only: the tool reads data/ from the checkout
whatrobot-taxonomy validate                               # 0 errors expected
whatrobot-taxonomy classify legs=4 integrated_arm=true    # → rb-3-1  Robot > Legged robot > Quadruped
whatrobot-taxonomy dist && whatrobot-taxonomy docs        # regenerate dist/ and docs/
pytest
```

Integrators who only need the data should download the release assets or read `dist/` directly; the Python package is for maintaining the taxonomy, not for consuming it.

## Integrations

| Integration | Direction | What it maps |
|---|---|---|
| `ifr-industrial` | both | arm leaves ↔ IFR industrial robot type classes (articulated, cartesian, SCARA, parallel, cylindrical) |
| `ifr-service` | from | `application` values → IFR professional / consumer / medical application groups |
| `iso-8373` | from | `iso_category` attribute → ISO 8373:2021 industrial / service / medical robot |
| `google` | from | seed — closest Google product categories; most categories explicitly unmapped |
| `shopify` | from | seed — closest Shopify Standard Product Taxonomy categories; most unmapped |

CI fails if any category is neither mapped nor explicitly listed as unmapped.

## Releases

CalVer (`YYYY-MM`), a stable release at most quarterly. `VERSION` on `main` names the release being prepared; the matching `CHANGELOG.md` section is marked *unreleased* until tagged. `whatrobot-taxonomy release 2026-04` sets `VERSION` and `pyproject.toml`, regenerates `dist/` and `docs/`, and dates the changelog section; pushing a `v2026-04` tag publishes the gzipped assets (CI checks the tag equals `VERSION`).

## Licence

- **Data** (`data/`, `dist/`, prose in `docs/`): [CC BY 4.0](data/LICENSE). Attribution: *"whatrobot taxonomy" by fysical.ai / whatro.bot, CC BY 4.0, https://github.com/fysical-ai/whatrobot-taxonomy*.
- **Code** (`whatrobot_taxonomy/`, `scripts/`, `tests/`, `schema/`): [MIT](LICENSE).

## Status

Pre-release. Product examples are illustrative placeholders used to test the classification rules; they are not verified product data. The `zh-Hans` localisation is an LLM draft awaiting native review. IFR type-class codes 40/50/90 and the Google/Shopify seed mappings (incl. Shopify `bi-18`) need a taxonomist's verification before the first stable release.

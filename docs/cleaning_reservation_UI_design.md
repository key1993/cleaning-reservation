# Cleaning Reservation UI Design

## Overview

Complete visual redesign of the EBSHER Admin Dashboard and Login page.
The old design used a purple gradient header with horizontal tabs. The new design
adopts a modern SaaS aesthetic — sidebar navigation, a warm off-white palette,
and a consistent design token system across all pages.

---

## Design System

### Typography
| Role | Font |
|------|------|
| UI / body | Plus Jakarta Sans (400, 500, 600, 700, 800) |
| Code / tokens / IDs | JetBrains Mono (400, 500, 600) |

Both fonts are loaded from Google Fonts.

### Color Palette (CSS custom properties)

| Variable | Value | Usage |
|----------|-------|-------|
| `--bg` | `#F6F4EF` | Page background |
| `--surface` | `#FFFFFF` | Cards, modals, sidebar |
| `--surface-2` | `#FBFAF7` | Table headers, secondary fills |
| `--border` | `#EBE7DE` | Default borders |
| `--text` | `#2C2A25` | Primary text |
| `--text-2` | `#6B665C` | Secondary text |
| `--text-3` | `#9C978B` | Muted / placeholder |
| `--accent` | `#2D6BDA` | Primary action color |
| `--accent-d` | `#1E54B8` | Hover state |
| `--accent-soft` | `#E5EFFC` | Active nav, focus ring |
| `--amber` | `#E08A12` | Pending status |
| `--teal` | `#0E9C8A` | Approved status |
| `--green` | `#2BA15F` | Active / success |
| `--rose` | `#DD5440` | Canceled / error / danger |
| `--blue` | `#2D6BDA` | Done status |
| `--gray` | `#8C887D` | Unknown / neutral |

### Shadows
- `--shadow-sm` — subtle card lift
- `--shadow-md` — raised elements
- `--shadow-lg` — modals and dropdowns

### Border Radius
- `--r-card: 14px` — cards and modals
- `--r: 10px` — buttons and inputs
- `--r-sm: 7px` — small elements (chips, cost edit)

---

## Files Changed

### 1. `templates/admin.html`
**Commit:** `b5a27b2`

#### Layout
- **Before:** Full-width header bar + horizontal tab buttons + scrollable container
- **After:** Fixed sidebar (240 px) + flexible main area with topbar and scrollable content

#### Sidebar
- EBSHER brand mark (logo + name + "Admin Panel" subtitle)
- Four nav items with live reservation / client / crew counts
- Active tab highlighted with accent-soft background
- User box (avatar, name, role) + Logout link at the bottom

#### Topbar
- Displays the current tab title and subtitle, updated dynamically on tab switch
- Live search box that filters table rows client-side

#### Tables
- **Before:** Purple gradient `<thead>`, large padding, 16 px font
- **After:** Subtle uppercase labels on `--surface-2`, compact 13.5 px font, sticky headers

#### Status Badges
| Status | Old class | New appearance |
|--------|-----------|----------------|
| Pending | `.badge-pending` | Amber pill with dot |
| Approved | `.badge-confirmed` | Teal pill with dot |
| Done | `.badge-done` | Blue pill with dot |
| Canceled | `.badge-canceled` | Rose pill with dot |
| Active | `.badge-active` | Green pill with dot |
| Disabled | `.badge-disabled` | Rose pill with dot |

#### Health Check Column (Clients tab)
- **Before:** Stacked dot + emoji + label per indicator
- **After:** Compact inline `hchip` chips (🏠 Brain / ⚡ Grid / ☀️ Inverter) with color-coded backgrounds

#### Cost Edit (Reservations tab)
- **Before:** Plain number input + separate save button
- **After:** Fused `cost-edit` component with inline `JOD` prefix and attached save button

#### Buttons
All existing `.btn-*` class names preserved. Visual updates:
- `btn-primary` → accent blue
- `btn-danger` → rose
- `btn-success` → green
- `btn-warning` → amber
- `btn-secondary` → ghost (surface + border)

#### Firebase Actions Dropdown
- **Before:** Purple gradient trigger button
- **After:** Dark (`#2E2B25`) trigger button with white text; menu items color-coded by action type

#### Modals
- Overlay: `rgba(38,32,18,.42)` + backdrop blur
- Modal box: white card with `--surface-2` header and footer strips
- Consistent with card border-radius and shadow system
- All modal IDs, form fields, and JavaScript hooks unchanged

#### Toast Notifications
- **Before:** Green pill, bottom-right
- **After:** Dark pill (`#2E2B25`), bottom-center, slide-up animation

---

### 2. `templates/admin_login.html`
**Commit:** `dfffc2a`

#### Layout
- Centered card on `--bg` background with subtle 40 px grid pattern overlay
- Card: white, 20 px border-radius, `--shadow-lg`

#### Brand section
- EBSHER logo in a teal→blue gradient mark (56 × 56 px, 16 px radius)
- Brand name + "Admin Panel" subtitle
- Horizontal divider separating brand from form

#### Form
- Label style: 12 px uppercase-weight, `--text-2`
- Inputs: 1 px border, focus ring using `--accent-soft`, 12 px border-radius
- Password toggle: icon button positioned inside the input
- Error state: rose soft background box with ⚠️ icon (replaces old red border-left card)
- Submit button: full-width, accent blue, subtle box-shadow

#### Preserved
- `method="POST"` form action
- Jinja2 `{% if error %}` error rendering
- `autofocus` on username field
- Password show/hide toggle logic

---

## What Was NOT Changed

- All Jinja2 template syntax (`{% %}` and `{{ }}`)
- All `fetch()` API endpoints
- All `id=""` attributes referenced by JavaScript
- All JavaScript function names and logic
- All form `action` attributes
- CSS class names used by JavaScript (`tab-btn`, `tab-content`, `active`, etc.)

---

## Git History

| Commit | File | Description |
|--------|------|-------------|
| `b5a27b2` | `templates/admin.html` | Redesign admin dashboard |
| `dfffc2a` | `templates/admin_login.html` | Redesign login page |

Repository: `https://github.com/key1993/cleaning-reservation.git`
Branch: `master`

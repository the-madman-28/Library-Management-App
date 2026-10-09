# Library Management System CSS

Link only `style.css` from `base.html`.

Files:
- variables.css — colors, radii, shadows, transitions
- base.css — reset, body, navbar, flash messages, footer
- layout.css — containers, page headers, date badge, generic panels
- dashboard.css — overview cards, action cards, dashboard sections
- tables.css — tables, read-only lists, status badges, empty states
- cards.css — reusable icon color classes
- responsive.css — tablet and mobile rules
- style.css — master file importing everything

In base.html:
<link rel="stylesheet" href="{{ url_for('static', filename='css/style.css') }}">

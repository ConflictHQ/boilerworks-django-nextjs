# Permission Comparison Tool - Quick Start Guide

## What is it?

A Django admin tool to compare group-based permissions between multiple users with an interactive, real-time interface.

## Quick Start (3 Steps)

### 1. Select Users
Go to **Admin → Users**, select 2+ users with checkboxes.

### 2. Run Action
Choose **"Compare user group permissions"** from Actions dropdown, click **Go**.

### 3. Compare
Click any user card to select as base user. The comparison table loads instantly showing:
- ✓ Green = Has group
- ✗ Red = Missing group
- Yellow highlight = Difference detected

## Key Features

- **HTMX-powered**: No page reloads, instant results
- **Visual comparison**: Color-coded status icons
- **Smart filtering**: Search groups by name
- **Direct access**: Click "View in Admin" to modify permissions
- **Organization-aware**: Shows only relevant groups

## Common Use Cases

### New Employee Onboarding
Select new employee + their manager → Compare → Add missing groups

### Permission Audit
Select all users in role → Compare against standard user → Fix inconsistencies

### Troubleshooting Access
Select affected user + working user → Compare → Identify missing permissions

## Tips

- **Use the filter**: Type group names to quickly find specific permissions
- **Look for yellow rows**: These highlight differences between users
- **Compare multiple bases**: Click different user cards to change perspective
- **Minimum 2 users**: Action requires at least 2 users selected

## Technical Details

- **Location**: `/app/core/core/compare-user-permissions/`
- **Technology**: Django + HTMX (no React/Vue needed)
- **Performance**: Handles 10+ users and 100+ groups smoothly
- **Security**: Staff-only access, organization-scoped

## Need Help?

See full documentation: `docs/admin_permission_comparison.md`

## Screenshots Flow

```
1. Admin User List
   [x] User A
   [x] User B
   [x] User C
   Actions: [Compare user group permissions ▼] [Go]

2. Comparison Page
   ┌─────────────┐  ┌─────────────┐  ┌─────────────┐
   │  User A     │  │  User B     │  │  User C     │
   │  (click)    │  │  john@...   │  │  jane@...   │
   └─────────────┘  └─────────────┘  └─────────────┘

3. Results Table (after clicking User A)
   ┌──────────────────────┬─────────┬─────────┬─────────┐
   │ Group Name           │ User A  │ User B  │ User C  │
   ├──────────────────────┼─────────┼─────────┼─────────┤
   │ ROLE: Admin          │    ✓    │    ✗    │    ✗    │ ← Yellow highlight
   │ ROLE: Manager        │    ✓    │    ✓    │    ✓    │
   │ GLOBAL: Platform Users  │    ✓    │    ✓    │    ✗    │ ← Yellow highlight
   └──────────────────────┴─────────┴─────────┴─────────┘
```

## Keyboard Shortcuts

- **Tab**: Navigate between user cards
- **Enter/Space**: Select focused user card
- **Type in filter**: Immediately filters groups

## Browser Support

Works in all modern browsers:
- Chrome/Edge 90+
- Firefox 88+
- Safari 14+
- Mobile browsers supported

---

**Ready to use!** Just select users and start comparing permissions.

# VivaCRM CSS Naming Convention

## Genel Kurallar

### 1. Component Naming (BEM-inspired)
```css
/* Block */
.viva-card { }

/* Element */
.viva-card__header { }
.viva-card__body { }
.viva-card__footer { }

/* Modifier */
.viva-card--primary { }
.viva-card--large { }
```

### 2. Utility Classes
```css
/* Prefix: u- */
.u-text-center { }
.u-mb-4 { }
.u-hidden { }
```

### 3. State Classes
```css
/* Prefix: is- veya has- */
.is-active { }
.is-disabled { }
.has-error { }
.has-children { }
```

### 4. JavaScript Hooks
```css
/* Prefix: js- */
.js-dropdown-toggle { }
.js-modal-trigger { }
```

## Component Örnekleri

### Card Component
```css
.viva-card {
  @apply bg-base-100 rounded-lg shadow-md;
}

.viva-card__header {
  @apply p-4 border-b border-base-200;
}

.viva-card__title {
  @apply text-lg font-semibold;
}

.viva-card__body {
  @apply p-4;
}

.viva-card__footer {
  @apply p-4 border-t border-base-200;
}

/* Modifiers */
.viva-card--primary {
  @apply border-2 border-primary;
}

.viva-card--compact {
  @apply p-2;
}
```

### Button Component
```css
.viva-btn {
  @apply btn;
}

.viva-btn--primary {
  @apply btn-primary;
}

.viva-btn--secondary {
  @apply btn-secondary;
}

.viva-btn--large {
  @apply btn-lg;
}

.viva-btn--small {
  @apply btn-sm;
}
```

### Form Component
```css
.viva-form {
  @apply space-y-4;
}

.viva-form__group {
  @apply form-control;
}

.viva-form__label {
  @apply label;
}

.viva-form__input {
  @apply input input-bordered;
}

.viva-form__error {
  @apply text-error text-sm mt-1;
}
```

## Tailwind Utility Kullanımı

### Kullanılacak Durumlar
- Spacing (margin, padding)
- Typography
- Colors
- Flexbox/Grid layouts
- Simple states (hover, focus)

### Custom Class Yazılacak Durumlar
- Complex components
- Repeated patterns
- JavaScript interactions
- Animation sequences

## Dosya Organizasyonu

```
static/css/src/
├── base/
│   ├── reset.css
│   ├── typography.css
│   ├── variables.css
│   └── theme.css
├── components/
│   ├── buttons.css
│   ├── cards.css
│   ├── forms.css
│   ├── modals.css
│   └── tables.css
├── layouts/
│   ├── dashboard.css
│   ├── navbar.css
│   └── sidebar.css
├── utilities/
│   ├── animations.css
│   ├── helpers.css
│   └── spacing.css
└── main.css
```

## Best Practices

1. **Specificity**: Mümkün olduğunca düşük specificity kullan
2. **!important**: Asla kullanma (utilities hariç)
3. **Nesting**: Maximum 3 seviye
4. **Variables**: CSS Custom Properties kullan
5. **Responsive**: Mobile-first yaklaşım

## Component Template

```css
/**
 * Component: [Component Name]
 * Description: [What this component does]
 * Usage: [Where this component is used]
 */

/* Base */
.viva-[component] {
  /* Base styles */
}

/* Elements */
.viva-[component]__[element] {
  /* Element styles */
}

/* Modifiers */
.viva-[component]--[modifier] {
  /* Modifier styles */
}

/* States */
.viva-[component].is-[state] {
  /* State styles */
}

/* Responsive */
@media (min-width: 768px) {
  .viva-[component] {
    /* Tablet+ styles */
  }
}

/* Dark Mode */
[data-theme="vivacrmDark"] .viva-[component] {
  /* Dark mode styles */
}
```
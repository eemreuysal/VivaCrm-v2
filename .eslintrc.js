module.exports = {
    "env": {
        "browser": true,
        "es2021": true,
        "node": true
    },
    "extends": [
        "eslint:recommended"
    ],
    "parserOptions": {
        "ecmaVersion": "latest",
        "sourceType": "module"
    },
    "globals": {
        "Alpine": "readonly",
        "htmx": "readonly",
        "ApexCharts": "readonly",
        "VivaCRM": "readonly"
    },
    "ignorePatterns": [
        "static/js/vendor/**/*",
        "static/js/dist/**/*",
        "staticfiles/**/*",
        "node_modules/**/*",
        "*.min.js"
    ],
    "rules": {
        "indent": ["error", 4],
        "linebreak-style": ["error", "unix"],
        "quotes": ["error", "single"],
        "semi": ["error", "always"],
        "no-unused-vars": ["warn", { "argsIgnorePattern": "^_" }],
        "no-console": ["warn", { "allow": ["warn", "error"] }],
        "arrow-parens": ["error", "always"],
        "object-curly-spacing": ["error", "always"],
        "array-bracket-spacing": ["error", "never"],
        "comma-dangle": ["error", "never"],
        "no-trailing-spaces": "error",
        "eol-last": ["error", "always"],
        "no-multiple-empty-lines": ["error", { "max": 2 }],
        "prefer-const": "error",
        "no-var": "error",
        "prefer-arrow-callback": "warn",
        "prefer-template": "warn",
        "no-eval": "error",
        "no-implied-eval": "error",
        "no-new-func": "error",
        "max-len": ["warn", { "code": 120 }],
        "no-prototype-builtins": "error"
    }
};
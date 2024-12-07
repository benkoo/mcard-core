module.exports = {
    "env": {
        "node": true,
        "es2021": true,
        "jest": true
    },
    "extends": [
        "eslint:recommended",
        "plugin:jest/recommended",
        "plugin:jest/style",
        "prettier"
    ],
    "plugins": [
        "jest"
    ],
    "parserOptions": {
        "ecmaVersion": "latest",
        "sourceType": "module"
    },
    "rules": {
        // Code Style
        "indent": ["error", 4],
        "linebreak-style": ["error", "unix"],
        "quotes": ["error", "single"],
        "semi": ["error", "always"],
        
        // Variables
        "no-unused-vars": ["warn", { 
            "argsIgnorePattern": "^_",
            "varsIgnorePattern": "^_"
        }],
        
        // Console Usage
        "no-console": ["warn", { 
            "allow": ["warn", "error", "info", "debug"]
        }],

        // Jest Specific Rules
        "jest/no-disabled-tests": "warn",
        "jest/no-focused-tests": "error",
        "jest/no-identical-title": "error",
        "jest/prefer-to-have-length": "warn",
        "jest/valid-expect": "error",
        "jest/expect-expect": ["error", { 
            "assertFunctionNames": ["expect", "request.**.expect"] 
        }],
        "jest/no-standalone-expect": ["error", { 
            "additionalTestBlockFunctions": ["beforeEach", "afterEach"] 
        }],
        
        // Best Practices
        "no-var": "error",
        "prefer-const": "warn",
        "eqeqeq": ["error", "always"],
        "curly": ["error", "all"],
        "no-multi-spaces": "error",
        "no-multiple-empty-lines": ["error", { 
            "max": 1,
            "maxEOF": 0 
        }],
        
        // ES6+ Features
        "arrow-body-style": ["error", "as-needed"],
        "prefer-arrow-callback": "warn",
        "prefer-template": "warn",
        "object-shorthand": "warn",
        
        // Async/Await
        "no-return-await": "warn",
        "require-await": "warn"
    },
    "overrides": [
        {
            "files": ["tests/**/*.js", "**/*.test.js"],
            "rules": {
                // Relaxed rules for test files
                "no-console": "off",
                "max-lines": "off",
                "max-lines-per-function": "off",
                
                // Stricter Jest-specific rules
                "jest/no-commented-out-tests": "error",
                "jest/no-mocks-import": "error",
                "jest/valid-title": ["error", {
                    "ignoreTypeOfDescribeName": true
                }]
            }
        }
    ],
    "settings": {
        "jest": {
            "version": 29
        }
    }
};

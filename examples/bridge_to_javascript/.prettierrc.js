module.exports = {
    // Basic Formatting
    printWidth: 100,
    tabWidth: 4,
    useTabs: false,
    semi: true,
    singleQuote: true,
    quoteProps: 'as-needed',
    
    // JSX Formatting
    jsxSingleQuote: false,
    jsxBracketSameLine: false,
    
    // Trailing Commas and Brackets
    trailingComma: 'es5',
    bracketSpacing: true,
    bracketSameLine: false,
    
    // Arrow Functions
    arrowParens: 'avoid',
    
    // Whitespace
    endOfLine: 'lf',
    
    // Special File Handling
    overrides: [
        {
            files: ['*.json', '*.yml', '*.yaml', '*.md'],
            options: {
                tabWidth: 2,
            },
        },
        {
            files: ['*.test.js', 'tests/**/*.js'],
            options: {
                printWidth: 120, // Allow longer lines in test files
            },
        },
    ],
};

module.exports = {
    hooks: {
        'pre-commit': 'lint-staged',
        'pre-push': 'npm test'
    }
};

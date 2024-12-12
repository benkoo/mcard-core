const fs = require('fs');
const path = require('path');

describe('Environment File Existence', () => {
    test('Check if .env file exists', () => {
        const envFilePath = path.resolve(__dirname, '../.env'); // Use absolute path
        console.log(`Checking for .env file at: ${envFilePath}`); // Print the path
        expect(fs.existsSync(envFilePath)).toBe(true);
    });
});


// Note that the above test uses path.resolve to create an absolute path to the .env file.
// This one used ".env" to access the file in the current directory.
describe('Environment File Existence', () => {
    test('Check if .env file exists with relative path', () => {
        const envFilePath = '.env';
        expect(fs.existsSync(envFilePath)).toBe(true);
    });
});


describe('Environment File Existence', () => {
    test('Check if .env file exists with absolute path', () => {
        const envFilePath = path.resolve(__dirname, '../.env'); // Create an absolute path
        console.log(`Current working directory: ${process.cwd()}`); // Log current working directory
        console.log(`Checking for .env file at: ${envFilePath}`); // Log resolved path
        expect(fs.existsSync(envFilePath)).toBe(true);
    });
});
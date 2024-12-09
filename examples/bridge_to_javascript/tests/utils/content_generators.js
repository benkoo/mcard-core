function generateLargeContent(sizeInBytes) {
  return 'x'.repeat(sizeInBytes);
}

function generateSpecialCharContent() {
  return `
    🌈 Unicode Emoji Test
    こんにちは World! 
    Special Chars: !@#$%^&*()_+{}:"<>?
    Accented: áéíóú
    Mathematical: ∑∏∫
  `;
}

module.exports = {
  generateLargeContent,
  generateSpecialCharContent
};

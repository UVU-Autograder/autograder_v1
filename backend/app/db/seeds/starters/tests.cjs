module.exports = ({ test, loadSubmission, assert }) => {
  test('main', 'page has a heading', async () => {
    const { document } = await loadSubmission();
    assert.ok(document.querySelector('h1'), 'The page needs an h1 heading.');
  });
};

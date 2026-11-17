(function () {
  const textarea = document.getElementById('textInput');
  const form = document.getElementById('analysisForm');
  if (!textarea || !form) return;

  const wordCount = document.getElementById('wordCount');
  const charCount = document.getElementById('charCount');
  const clearButton = document.getElementById('clearText');
  const analyzeButton = document.getElementById('analyzeButton');
  const errorBox = document.getElementById('clientError');

  function updateCounts() {
    const words = textarea.value.trim().match(/\b[\w']+\b/g) || [];
    wordCount.textContent = `${words.length} ${words.length === 1 ? 'word' : 'words'}`;
    charCount.textContent = `${textarea.value.length.toLocaleString()} / 10,000 characters`;
  }
  textarea.addEventListener('input', updateCounts);
  updateCounts();

  clearButton.addEventListener('click', () => {
    textarea.value = '';
    updateCounts();
    textarea.focus();
    const results = document.getElementById('results');
    if (results) results.classList.add('d-none');
    errorBox.classList.add('d-none');
  });

  form.addEventListener('submit', async (event) => {
    event.preventDefault();
    if (!textarea.value.trim()) {
      errorBox.textContent = 'Enter some text to analyze.';
      errorBox.classList.remove('d-none');
      textarea.focus();
      return;
    }
    errorBox.classList.add('d-none');
    analyzeButton.disabled = true;
    analyzeButton.querySelector('span:first-child').textContent = 'Checking…';
    try {
      const response = await fetch(form.action, {
        method: 'POST',
        body: new FormData(form),
        headers: { 'X-Requested-With': 'XMLHttpRequest' }
      });
      const contentType = response.headers.get('content-type') || '';
      if (!contentType.includes('application/json')) {
        const body = await response.text();
        throw new Error(response.ok
          ? 'The server returned an unexpected page. Reload and try again.'
          : 'The server could not analyze this text. Check the Django server console for details.');
      }
      const data = await response.json();
      if (!response.ok) throw new Error(data.error || 'Something went wrong. Please try again.');
      // The saved review page renders the result with Django's normal escaping.
      window.location.href = `/history/${data.analysis_id}/`;
    } catch (error) {
      errorBox.textContent = error.message;
      errorBox.classList.remove('d-none');
    } finally {
      analyzeButton.disabled = false;
      analyzeButton.querySelector('span:first-child').textContent = 'Check my writing';
    }
  });
})();

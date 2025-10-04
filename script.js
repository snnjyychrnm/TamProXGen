const API_BASE = "http://localhost:8000"; // Update if hosted elsewhere

// Format AI Explanation - clean markdown (**text**) to HTML <strong>text</strong>
function formatExplanation(text) {
  return `<div class="ai-box">${text
    .replace(/\\(.?)\\/g, "<strong>$1</strong>")
    .replace(/\n/g, "<br>")
  }</div>`;
}

// Search functionality - Enhanced with loading animation
async function searchProverb() {
  const input = document.getElementById("searchInput").value.trim();
  const searchResults = document.getElementById("searchResults");

  if (!input) {
    searchResults.innerHTML = `<div class="error">Please enter a proverb to search</div>`;
    return;
  }

  searchResults.innerHTML = `
    <div class="loading">
      <div class="loader"></div>
      <p>Searching for "${input}"...</p>
    </div>`;

  try {
    const res = await fetch(`${API_BASE}/search/`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ input_text: input })
    });

    const data = await res.json();

    if (data.found) {
      const r = data.result;
      searchResults.innerHTML = `
        <div class="result-card">
          <h3>✅ Match Found</h3>
          <div class="result-item"><span class="label">📜 Tamil:</span><span class="value">${r.Proverb_Tamil}</span></div>
          <div class="result-item"><span class="label">🔡 Transliteration:</span><span class="value">${r.Transliteration}</span></div>
          <div class="result-item"><span class="label">📝 Meaning (Tamil):</span><span class="value">${r.Meaning_Tamil}</span></div>
          <div class="result-item"><span class="label">🌍 Meaning (English):</span><span class="value">${r.Meaning_English}</span></div>
          <div class="result-item"><span class="label">💬 Example (Tamil):</span><span class="value">${r.Example_Tamil}</span></div>
          <div class="result-item"><span class="label">📘 Example (English):</span><span class="value">${r.Example_English}</span></div>
          <div class="result-item"><span class="label">🎭 Type:</span><span class="value">${r.Type}</span></div>
        </div>`;
    } else {
      searchResults.innerHTML = `
        <div class="result-card ai-result">
          <h3>🤖 AI Generated Explanation</h3>
          ${formatExplanation(data.generated)}
        </div>`;
    }
  } catch (err) {
    searchResults.innerHTML = `
      <div class="error">
        <p>❌ Error: ${err.message}</p>
        <button class="retry-btn" onclick="searchProverb()">Retry</button>
      </div>`;
  }
}

// Filter functionality
async function filterProverbs() {
  const type = document.getElementById("filterType").value;
  const keyword = document.getElementById("filterKeyword").value.trim();
  const filterResults = document.getElementById("filterResults");

  filterResults.innerHTML = `
    <div class="loading">
      <div class="loader"></div>
      <p>Filtering proverbs...</p>
    </div>`;

  try {
    const res = await fetch(`${API_BASE}/filter/`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ type, keyword })
    });

    const data = await res.json();

    if (data.results.length) {
      let html = `
        <div class="table-wrapper">
          <table class="proverb-table">
            <thead>
              <tr>
                <th>Proverb (Tamil)</th>
                <th>Meaning (English)</th>
                <th>Type</th>
              </tr>
            </thead>
            <tbody>`;

      data.results.forEach(row => {
        html += `
          <tr>
            <td>${row["Proverb (Tamil)"]}</td>
            <td>${row["Meaning (English)"]}</td>
            <td class="type-${row["Literal/Figurative"].toLowerCase()}">${row["Literal/Figurative"]}</td>
          </tr>`;
      });

      html += `</tbody></table></div>`;
      filterResults.innerHTML = html;
    } else {
      filterResults.innerHTML = `
        <div class="no-results">
          <p>No proverbs found matching your criteria.</p>
          <button class="action" onclick="filterProverbs()">Try Again</button>
        </div>`;
    }
  } catch (err) {
    filterResults.innerHTML = `
      <div class="error">
        <p>❌ Error: ${err.message}</p>
        <button class="retry-btn" onclick="filterProverbs()">Retry</button>
      </div>`;
  }
}

// Voice input
function startVoiceInput() {
  const recognition = new (window.SpeechRecognition || window.webkitSpeechRecognition)();
  const micBtn = document.getElementById("micBtn");
  const searchInput = document.getElementById("searchInput");
  const searchResults = document.getElementById("searchResults");

  recognition.lang = "ta-IN";
  micBtn.innerHTML = '🎤 Listening...';
  micBtn.classList.add('recording');

  recognition.start();

  recognition.onresult = function(event) {
    const transcript = event.results[0][0].transcript;
    searchInput.value = transcript;
    micBtn.innerHTML = '🎙 Voice Input';
    micBtn.classList.remove('recording');
    searchProverb();
  };

  recognition.onerror = function(event) {
    micBtn.innerHTML = '🎙 Voice Input';
    micBtn.classList.remove('recording');
    searchResults.innerHTML = `
      <div class="error">
        <p>🎤 Voice input failed: ${event.error}</p>
        <button class="retry-btn" onclick="startVoiceInput()">Try Again</button>
      </div>`;
  };
}

// Attach event listeners after DOM loads
document.addEventListener("DOMContentLoaded", () => {
  document.getElementById("searchBtn").addEventListener("click", searchProverb);
  document.getElementById("micBtn").addEventListener("click", startVoiceInput);
  document.getElementById("filterBtn").addEventListener("click", filterProverbs);

  document.getElementById("searchInput").addEventListener("keypress", (e) => {
    if (e.key === "Enter") searchProverb();
  });

  document.getElementById("filterKeyword").addEventListener("keypress", (e) => {
    if (e.key === "Enter") filterProverbs();
  });
});

(function () {
  const chatLog = document.getElementById('chatLog');
  const composer = document.getElementById('composer');
  const input = document.getElementById('messageInput');
  const sendBtn = document.getElementById('sendBtn');
  const resetBtn = document.getElementById('resetBtn');
  const chips = document.querySelectorAll('.chip');

  // Per-browser-tab session id so the server can keep short AI conversation history
  const sessionId = 'sess_' + Math.random().toString(36).slice(2);

  function scrollToBottom() {
    chatLog.scrollTop = chatLog.scrollHeight;
  }

  function addUserMessage(text) {
    const wrap = document.createElement('div');
    wrap.className = 'msg user';
    wrap.innerHTML = `<div class="bubble"><p></p></div>`;
    wrap.querySelector('p').textContent = text;
    chatLog.appendChild(wrap);
    scrollToBottom();
  }

  function addTypingIndicator() {
    const wrap = document.createElement('div');
    wrap.className = 'msg bot';
    wrap.id = 'typingIndicator';
    wrap.innerHTML = `
      <div class="bubble">
        <div class="typing-dots"><span></span><span></span><span></span></div>
      </div>`;
    chatLog.appendChild(wrap);
    scrollToBottom();
  }

  function removeTypingIndicator() {
    const el = document.getElementById('typingIndicator');
    if (el) el.remove();
  }

  function badgeFor(source, confidence) {
    if (source === 'ai') {
      return `<span class="badge ai">🧠 ai</span>`;
    }
    if (source === 'error') {
      return `<span class="badge error">⚠ error</span>`;
    }
    // skill or nlp (local engine)
    const conf = (confidence !== undefined && confidence !== null)
      ? `<span class="confidence">conf ${confidence}</span>` : '';
    return `<span class="badge instant">⚡ instant</span>${conf}`;
  }

  function addBotMessage(reply, source, confidence) {
    const wrap = document.createElement('div');
    wrap.className = 'msg bot';
    const bubbleClass = source === 'error' ? 'bubble error' : 'bubble';
    wrap.innerHTML = `
      <div class="${bubbleClass}"><p></p></div>
      <div class="badge-row">${badgeFor(source, confidence)}</div>
    `;
    wrap.querySelector('p').textContent = reply;
    chatLog.appendChild(wrap);
    scrollToBottom();
  }

  async function sendMessage(text) {
    text = text.trim();
    if (!text) return;

    addUserMessage(text);
    input.value = '';
    sendBtn.disabled = true;
    addTypingIndicator();

    try {
      const res = await fetch('/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: text, session_id: sessionId }),
      });
      const data = await res.json();
      removeTypingIndicator();
      addBotMessage(data.reply, data.source, data.confidence);
    } catch (err) {
      removeTypingIndicator();
      addBotMessage(
        "Couldn't reach the server. Is the Flask app still running?",
        'error'
      );
    } finally {
      sendBtn.disabled = false;
      input.focus();
    }
  }

  composer.addEventListener('submit', (e) => {
    e.preventDefault();
    sendMessage(input.value);
  });

  chips.forEach((chip) => {
    chip.addEventListener('click', () => {
      sendMessage(chip.dataset.text);
    });
  });

  resetBtn.addEventListener('click', async () => {
    await fetch('/api/reset', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ session_id: sessionId }),
    });
    chatLog.innerHTML = '';
    addBotMessage(
      "Conversation reset. Ask me anything!",
      'skill',
      null
    );
  });

  input.focus();
})();

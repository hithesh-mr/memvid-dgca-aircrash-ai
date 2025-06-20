document.addEventListener('DOMContentLoaded', () => {
  const sendBtn = document.getElementById('send-btn');
  const userInput = document.getElementById('user-input');
  const chatWindow = document.getElementById('chat-window');

  function appendMessage(text, className) {
    const msg = document.createElement('div');
    msg.className = `message ${className}`;
    msg.textContent = text;
    chatWindow.appendChild(msg);
    chatWindow.scrollTop = chatWindow.scrollHeight;
  }

  function botReply(question) {
    // Placeholder response; replace with real backend integration
    const reply = `🔎 Sherlock is investigating: "${question}"`;
    appendMessage(reply, 'bot');
  }

  function sendMessage() {
    const text = userInput.value.trim();
    if (!text) return;
    appendMessage(text, 'user');
    userInput.value = '';
    setTimeout(() => botReply(text), 800);
  }

  sendBtn.addEventListener('click', sendMessage);
  userInput.addEventListener('keydown', (e) => {
    if (e.key === 'Enter') {
      e.preventDefault();
      sendMessage();
    }
  });
});
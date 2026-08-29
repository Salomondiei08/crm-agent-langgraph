const $ = (selector) => document.querySelector(selector);
const nodes = [...document.querySelectorAll('.node')];
let threadId = `browser-${Date.now()}`;

const setStatus = (label, mode) => { const status = $('#status'); status.textContent = label; status.className = `pill ${mode}`; };
const paint = (events, paused) => {
  nodes.forEach((node) => { node.classList.remove('active', 'done', 'waiting'); });
  const names = events.map((event) => event.split(':')[0]);
  nodes.forEach((node) => { if (names.includes(node.dataset.node)) node.classList.add('done'); });
  const waiting = paused ? nodes.find((node) => node.dataset.node === 'human_review') : nodes.find((node) => node.dataset.node === 'finalize');
  if (waiting) waiting.classList.add(paused ? 'waiting' : 'active');
};
const render = (data) => {
  setStatus(data.status === 'paused' ? 'WAITING FOR YOU' : 'COMPLETED', data.status);
  $('#category').textContent = data.category || '—'; $('#reply').textContent = data.draft || 'No reply yet.';
  $('#events').innerHTML = data.events.map((event) => `<span>${event}</span>`).join('');
  $('#approval').classList.toggle('hidden', data.status !== 'paused'); paint(data.events, data.status === 'paused');
};
const post = async (path, body) => { const response = await fetch(path, {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify(body)}); const data = await response.json(); if (!response.ok) throw new Error(data.error); return data; };
$('#run').onclick = async () => { $('#run').disabled = true; setStatus('RUNNING…', 'paused'); try { render(await post('/api/run', {ticket:$('#ticket').value, thread_id:threadId})); } catch (error) { $('#reply').textContent = error.message; } finally { $('#run').disabled = false; } };
document.querySelectorAll('[data-example]').forEach((button) => { button.onclick = () => { $('#ticket').value = button.dataset.example; }; });
['approve','reject'].forEach((decision) => { $(`#${decision}`).onclick = async () => { try { render(await post('/api/resume', {thread_id:threadId, decision})); } catch (error) { $('#reply').textContent = error.message; } }; });
$('#thread').textContent = threadId;

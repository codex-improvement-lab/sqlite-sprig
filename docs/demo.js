'use strict';
const data = window.SPRIG_DEMO;
const cardPicker = document.getElementById('card');
const branch = document.getElementById('branch');
const reduceMotion = window.matchMedia('(prefers-reduced-motion: reduce)');
const text = (id, value) => { document.getElementById(id).textContent = value; };
let animationTimer;

function selectCard(animate = true) {
  const id = cardPicker.value;
  const item = data.cases[id];
  const rows = item.rows;
  text('root-id', '#' + id);
  text('branch-title', 'Card ' + id + ' and its required context');
  text('space-name', rows.spaces.map(row => row.name).join(' · '));
  text('board-name', rows.boards.map(row => row.name).join(' · '));
  text('people-names', rows.users.map(row => row.name).join(' · '));
  text('label-names', rows.labels.map(row => row.name).join(' · '));
  for (const table of ['spaces', 'boards', 'users', 'labels', 'comments', 'card_labels']) text(table + '-count', rows[table].length);
  for (const id of ['root-id', 'space-name', 'board-name', 'people-names', 'label-names', 'spaces-count', 'boards-count', 'users-count', 'labels-count', 'comments-count', 'card_labels-count']) text('m-' + id, document.getElementById(id).textContent);
  text('kept', item.totalRows);
  text('omitted', data.sourceRows - item.totalRows);
  text('command-text', `python sqlite_sprig.py board.sqlite3 --root cards --where "id=${id}" --out card-${id}.sqlite3`);
  document.getElementById('download').href = 'data/' + item.filename;
  document.getElementById('download').setAttribute('aria-label', `Download SQLite file for card ${id}, ${item.totalRows} retained rows`);
  text('copy-status', '');
  branch.classList.remove('changing');
  clearTimeout(animationTimer);
  if (animate && !reduceMotion.matches) {
    requestAnimationFrame(() => {
      branch.classList.add('changing');
      animationTimer = setTimeout(() => branch.classList.remove('changing'), 650);
    });
  }
}

cardPicker.addEventListener('change', selectCard);
document.getElementById('copy').addEventListener('click', async () => {
  const command = document.getElementById('command-text').textContent;
  try {
    await navigator.clipboard.writeText(command);
    text('copy-status', 'Command copied.');
  } catch {
    const selection = window.getSelection();
    const range = document.createRange();
    range.selectNodeContents(document.getElementById('command-text'));
    selection.removeAllRanges();
    selection.addRange(range);
    text('copy-status', 'Command selected. Press Ctrl+C or ⌘C to copy.');
  }
});
selectCard(false);

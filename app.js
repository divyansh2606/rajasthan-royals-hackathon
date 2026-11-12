const players = {
  batters: [
    ['Tristan Stubbs', 90.13, 944, 516, 181.06, 68.99, 34], ['Liam Livingstone', 87.39, 812, 415, 192.33, 67.73, 30], ['Shreyas Iyer', 87.28, 860, 434, 194.77, 54.85, 29], ['Glenn Phillips', 86.94, 586, 307, 187.01, 55.01, 22], ['Rinku Singh', 86.28, 1238, 689, 178.40, 61.28, 49], ['Naman Dhir', 86.26, 427, 213, 193.75, 45.59, 16], ['Donovan Ferreira', 85.88, 313, 161, 187.02, 55.84, 10], ['Suryakumar Yadav', 85.32, 1378, 683, 199.36, 44.92, 41], ['Sikandar Raza', 84.98, 558, 305, 179.89, 65.65, 21], ['Rishabh Pant', 84.19, 625, 335, 183.40, 58.43, 24]
  ],
  bowlers: [
    ['Akeal Hosein', 89.31, 295, 235, 7.81, -0.09, 25], ['Matthew Humphreys', 87.50, 91, 85, 7.38, 0.09, 14], ['Sunil Narine', 85.24, 416, 393, 6.63, 0.38, 32], ['Jasprit Bumrah', 84.19, 816, 668, 7.45, -0.44, 55], ['Spencer Johnson', 82.00, 145, 102, 8.82, 0.61, 9], ['George Linde', 81.78, 63, 49, 8.53, -0.44, 8], ['Matheesha Pathirana', 81.59, 934, 630, 8.94, -0.80, 61], ['Kuldeep Yadav', 80.37, 699, 507, 8.36, -0.51, 43], ['Hasan Mahmud', 80.03, 166, 126, 8.29, -0.41, 14], ['Sakib Hussain', 79.92, 170, 120, 8.76, 1.25, 10]
  ]
};

// Portraits are externally hosted player-profile images found via web search.
// The initials fallback keeps the dashboard usable if a host blocks hotlinking.
const playerPhotos = {
  'Tristan Stubbs': 'https://images.icc-cricket.com/image/upload/t_player-headshot-portrait-lg-webp/prd/assets/players/8322/74761.png',
  'Liam Livingstone': 'https://images.icc-cricket.com/image/upload/t_player-headshot-portrait-lg-webp/prd/assets/players/6122/63940.png',
  'Shreyas Iyer': 'https://documents.bcci.tv/playerheadshot/bcci/1000x1280/1563.png',
  'Glenn Phillips': 'https://images.icc-cricket.com/image/upload/t_player-headshot-portrait-lg-webp/prd/assets/players/8322/65295.png',
  'Rinku Singh': 'https://documents.bcci.tv/resizedimageskirti/11087_compress.png',
  'Naman Dhir': 'https://img1.hscicdn.com/image/upload/f_auto%2Ct_ds_square_w_640%2Cq_50/lsci/db/PICTURES/CMS/381300/381384.png',
  'Donovan Ferreira': 'https://staticg.sportskeeda.com/editor/2026/01/fed3d-17677298680048-1920.jpg?w=668',
  'Suryakumar Yadav': 'https://images.icc-cricket.com/image/upload/t_player-headshot-portrait-lg-webp/prd/assets/players/generic/colored/11803.png',
  'Sikandar Raza': 'https://images.icc-cricket.com/image/upload/t_player-headshot-portrait-lg-webp/prd/assets/players/generic/colored/25422.png',
  'Rishabh Pant': 'https://documents.bcci.tv/resizedimageskirti/2972_compress.png',
  'Akeal Hosein': 'https://images.icc-cricket.com/image/upload/t_player-headshot-portrait-lg-webp/prd/assets/players/13203/57239.png',
  'Matthew Humphreys': 'https://images.icc-cricket.com/image/upload/t_player-headshot-portrait-lg-webp/prd/assets/players/13203/85951.png',
  'Sunil Narine': 'https://cricviz-westindies-production.s3.amazonaws.com/images/716a484a-1935-40b4-b710-7b1808c467bf.original.jpg',
  'Jasprit Bumrah': 'https://documents.bcci.tv/resizedimageskirti/1124_compress.png',
  'Spencer Johnson': 'https://images.icc-cricket.com/image/upload/t_player-headshot-portrait-lg-webp/prd/assets/players/generic/colored/67778.png',
  'George Linde': 'https://images.icc-cricket.com/image/upload/t_player-headshot-portrait-lg-webp/prd/assets/players/13203/57533.png',
  'Matheesha Pathirana': 'https://images.icc-cricket.com/image/upload/t_player-headshot-portrait-lg-webp/prd/assets/players/13203/73830.png',
  'Kuldeep Yadav': 'https://documents.bcci.tv/resizedimageskirti/261_compress.png',
  'Hasan Mahmud': 'https://static-files.cricket-australia.pulselive.com/headshots/440/3903-camedia.png',
  'Sakib Hussain': 'https://www.kkr.in/static-assets/images/players/99098.png?v=112.13'
};

let activeRole = 'batters';
const cards = document.querySelector('#cards');
const spotlightCards = document.querySelector('#spotlight-cards');
const dialog = document.querySelector('#detail-dialog');
const initials = name => name.split(' ').map(part => part[0]).join('').slice(0, 2);

function renderCards() {
  cards.innerHTML = players[activeRole].map((player, index) => {
    const [name, rating, valueA, valueB, metric, delta] = player;
    const metricName = activeRole === 'batters' ? 'pressure SR' : 'pressure econ';
    const volume = activeRole === 'batters' ? 'pressure balls' : 'legal balls';
    const reason = activeRole === 'batters'
      ? `Selected for a ${metric} pressure SR, ${delta > 0 ? '+' : ''}${delta} versus normal.`
      : `Selected for ${metric} pressure economy and ${player[6]} pressure wickets.`;
    return `<button class="player-card" data-index="${index}"><div class="avatar"><img src="${playerPhotos[name]}" alt="${name}" loading="lazy" onerror="this.style.display='none';this.parentElement.dataset.fallback='${initials(name)}'"></div><div><div class="rank">RANK ${String(index + 1).padStart(2, '0')}</div><div class="player-name">${name}</div><div class="player-meta">${metricName} ${metric} · ${valueB} ${volume}</div><div class="selection-reason">${reason}</div></div><div class="rating"><strong>${rating}</strong><small>ROBUST SCORE</small></div></button>`;
  }).join('');
  document.querySelectorAll('.player-card').forEach(card => card.addEventListener('click', () => showDetail(players[activeRole][card.dataset.index], Number(card.dataset.index) + 1)));
}

function renderSpotlight() {
  const leaders = [
    { role: 'batters', label: 'Top batter', statLabel: 'pressure SR', player: players.batters[0] },
    { role: 'bowlers', label: 'Top bowler', statLabel: 'pressure econ', player: players.bowlers[0] }
  ];
  spotlightCards.innerHTML = leaders.map(({ role, label, statLabel, player }) => `
    <button class="spotlight-card" data-role="${role}">
      <span class="spotlight-label">${label}</span><span class="spotlight-arrow" aria-hidden="true">↗</span>
      <strong>${player[0]}</strong><span class="spotlight-stat">${statLabel} ${player[4]} <i>·</i> score ${player[1]}</span>
      <span class="spotlight-action">View selection reason</span>
    </button>`).join('');
  spotlightCards.querySelectorAll('.spotlight-card').forEach((card, index) => card.addEventListener('click', () => {
    activeRole = leaders[index].role;
    document.querySelectorAll('.tab').forEach(tab => {
      tab.classList.toggle('active', tab.dataset.role === activeRole);
      tab.setAttribute('aria-selected', tab.dataset.role === activeRole);
    });
    renderCards();
    showDetail(leaders[index].player, 1);
  }));
}

function showDetail(player, rank) {
  const [name, rating, valueA, valueB, metric, delta, volume] = player;
  const batter = activeRole === 'batters';
  const why = batter
    ? `${name} is selected because they combined a ${metric} pressure strike rate with a ${delta > 0 ? '+' : ''}${delta} uplift over their own normal baseline.`
    : `${name} is selected because they combined a ${metric} pressure economy with ${volume} pressure wickets.`;
  document.querySelector('#detail-content').innerHTML = `<p class="eyebrow">${batter ? 'Batter' : 'Bowler'} · Rank ${rank}</p><h2 class="dialog-name">${name}</h2><p class="dialog-rating">ROBUST PRESSURE RATING ${rating}</p><div class="stats"><div class="stat"><strong>${valueA}</strong><span>${batter ? 'pressure runs' : 'pressure runs conceded'}</span></div><div class="stat"><strong>${valueB}</strong><span>${batter ? 'pressure balls' : 'pressure legal balls'}</span></div><div class="stat"><strong>${metric}</strong><span>${batter ? 'shrunk pressure SR' : 'shrunk pressure economy'}</span></div></div><p class="detail-text"><b>Why selected:</b> ${why} This ranking combines a primary pressure scenario with a stricter final-overs and chase-stress scenario.</p>`;
  dialog.showModal();
}

document.querySelectorAll('.tab').forEach(tab => tab.addEventListener('click', () => { activeRole = tab.dataset.role; document.querySelectorAll('.tab').forEach(item => { item.classList.toggle('active', item === tab); item.setAttribute('aria-selected', item === tab); }); renderCards(); }));
document.querySelector('.close').addEventListener('click', () => dialog.close());
renderSpotlight();
renderCards();

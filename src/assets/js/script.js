// Script para animação de hover do botão
document.getElementById('clean-crow-btn').addEventListener('mouseenter', function() {
  this.style.transition = '0.3s';
  this.style.transform = 'scale(1.1)';
});

document.getElementById('clean-crow-btn').addEventListener('mouseleave', function() {
  this.style.transition = '0.3s';
  this.style.transform = 'scale(1)';
});
// Script para animação de hover do botão
document.getElementById('clean-crow-btn').addEventListener('mouseenter', function() {
  this.style.transition = '0.3s';
  this.style.transform = 'scale(1.1)';
});

document.getElementById('clean-crow-btn').addEventListener('mouseleave', function() {
  this.style.transition = '0.3s';
  this.style.transform = 'scale(1)';
});

// Animação para simular atualização do log
function addRandomLogEntry() {
  const logContent = document.querySelector('.log-content');
  if (!logContent) return;
  
  const operations = [
    'Limpando cache do Chrome...',
    'Limpando cache do Firefox...',
    'Esvaziando lixeira...',
    'Removendo arquivos temporários...',
    'Limpando logs do sistema...',
    'Otimizando inicialização...',
    'Desfragmentando disco...',
    'Limpando DNS cache...'
  ];
  
  const randomOp = operations[Math.floor(Math.random() * operations.length)];
  const time = new Date().toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit', second: '2-digit' });
  
  const newEntry = document.createElement('div');
  newEntry.className = 'log-entry';
  newEntry.innerHTML = `
    <span class="log-time">[${time}]</span>
    <span class="log-message info">▶️ Iniciando: ${randomOp}</span>
  `;
  
  logContent.appendChild(newEntry);
  
  // Manter apenas as últimas 20 entradas
  while (logContent.children.length > 20) {
    logContent.removeChild(logContent.firstChild);
  }
  
  // Scroll automático para o final
  logContent.scrollTop = logContent.scrollHeight;
}

// Atualizar barra de progresso aleatoriamente
function updateProgress() {
  const progressBar = document.querySelector('.progress-bar-fill');
  const progressPercent = document.querySelector('.progress-percent');
  const progressCounter = document.querySelector('.progress-counter');
  const operationValue = document.querySelector('.operation-value');
  
  if (!progressBar || !progressPercent || !progressCounter || !operationValue) return;
  
  const currentWidth = parseInt(progressBar.style.width) || 0;
  const operations = [
    'Desfragmentando disco...',
    'Limpando arquivos temporários...',
    'Removendo programas...',
    'Limpando cache...',
    'Otimizando sistema...',
    'Atualizando programas...'
  ];
  
  if (currentWidth < 100) {
    const newWidth = Math.min(currentWidth + Math.floor(Math.random() * 10) + 1, 100);
    progressBar.style.width = newWidth + '%';
    progressPercent.textContent = newWidth + '%';
    
    const completed = Math.floor(newWidth / 100 * 34);
    progressCounter.textContent = completed + '/34';
    
    if (Math.random() > 0.7) {
      operationValue.textContent = operations[Math.floor(Math.random() * operations.length)];
    }
  }
}

// Iniciar simulações quando a página carregar
document.addEventListener('DOMContentLoaded', function() {
  // Adicionar entradas de log periodicamente
  setInterval(addRandomLogEntry, 3000);
  
  // Atualizar progresso periodicamente
  setInterval(updateProgress, 2000);
  
  // Inicializar AOS
  AOS.init({
    duration: 800,
    easing: 'ease-in-out',
    once: true
  });
  
  // Navbar scroll effect
  $(window).scroll(function () {
    if ($(this).scrollTop() > 50) {
      $('.navbar').addClass('scrolled');
    } else {
      $('.navbar').removeClass('scrolled');
    }
  });
  
  // Smooth scrolling for anchor links
  $('a[href*="#"]').on('click', function (e) {
    e.preventDefault();
    $('html, body').animate(
      {
        scrollTop: $($(this).attr('href')).offset().top - 70,
      },
      500,
      'linear'
    );
  });
});
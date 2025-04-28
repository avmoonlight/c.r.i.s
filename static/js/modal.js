// Função para abrir o modal
function abrirModal(id) {
    const modal = document.getElementById(`modal-${id}`);
    if (modal) {
        modal.style.display = 'flex';
    }
}

// Função para fechar o modal
function fecharModal(id) {
    const modal = document.getElementById(`modal-${id}`);
    if (modal) {
        modal.style.display = 'none';
    }
}

// Fecha o modal ao clicar fora da área de conteúdo
window.addEventListener('click', function(event) {
    const modals = document.querySelectorAll('.modal');
    modals.forEach(function(modal) {
        if (event.target === modal) {
            modal.style.display = 'none';
        }
    });
});

// Permite fechar o modal com a tecla ESC
window.addEventListener('keydown', function(event) {
    if (event.key === 'Escape') {
        const modals = document.querySelectorAll('.modal');
        modals.forEach(function(modal) {
            if (modal.style.display === 'flex') {
                modal.style.display = 'none';
            }
        });
    }
});
